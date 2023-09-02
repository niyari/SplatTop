import datetime as dt

import sqlalchemy as db
from flask import Flask, render_template, request
from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker

from splat_top.constants import MODES, REGIONS
from splat_top.db import create_uri
from splat_top.sql_types import Player, Schedule
from splat_top.utils import get_seasons

app = Flask(__name__)
engine = db.create_engine(create_uri())


@app.route("/")
def leaderboard():
    Session = sessionmaker(bind=engine)
    session = Session()

    mode = request.args.get("mode", "Splat Zones")
    region = request.args.get("region", "Tentatek")

    subquery = (
        session.query(
            Player.mode, func.max(Player.timestamp).label("latest_timestamp")
        )
        .group_by(Player.mode)
        .subquery()
    )

    players = (
        session.query(Player)
        .join(
            subquery,
            (subquery.c.latest_timestamp == Player.timestamp)
            & (subquery.c.mode == Player.mode),
        )
        .filter(Player.mode == mode)
        .filter(Player.region == region)
        .order_by(Player.mode.asc())
        .order_by(Player.region.asc())
        .order_by(Player.rank.asc())
        .all()
    )

    session.close()
    return render_template(
        "leaderboard.html",
        players=players,
        modes=MODES,
        regions=REGIONS,
        mode=mode,
        region=region,
    )


@app.route("/player/<string:player_id>")
def player_detail(player_id):
    Session = sessionmaker(bind=engine)
    session = Session()

    player = (
        session.query(Player)
        .filter_by(id=player_id)
        .order_by(Player.timestamp.desc())
        .first()
    )
    aliases = (
        session.query(
            func.concat(Player.name, "#", Player.name_id).label("alias"),
            func.max(Player.timestamp).label("last_seen"),
        )
        .filter(Player.id == player_id)
        .group_by("alias")
        .all()
    )
    aliases_data = [
        {
            "alias": alias[0],
            "last_seen": alias[1].strftime("%Y-%m-%d"),
        }
        for alias in aliases
        if alias[0] != f"{player.name}#{player.name_id}"
    ]
    peak_data = []

    modes_data = {}
    for mode in MODES:
        print("MODE", mode)
        m_data = (
            session.query(
                Player.timestamp,
                Player.x_power,
                Schedule.stage_1_name,
                Schedule.stage_2_name,
                Player.weapon,
                Player.rank,
            )
            .join(
                Schedule,
                Schedule.start_time == Player.rotation_start,
                isouter=True,
            )
            .filter(Player.id == player_id, Player.mode == mode)
            .all()
        )
        modes_data[mode] = [
            {
                "timestamp": x[0].isoformat(),
                "x_power": x[1],
                "stage_1": x[2]
                if x[2] is not None
                else "Missing Schedule Data",
                "stage_2": x[3]
                if x[3] is not None
                else "Missing Schedule Data",
                "weapon": x[4],
                "rank": x[5],
            }
            for x in m_data
        ]

        # Get latest rank
        current_rank = (
            session.query(Player.rank, Player.weapon)
            .filter_by(id=player_id, mode=mode)
            .order_by(Player.timestamp.desc())
            .first()
        )
        if current_rank is None:
            continue
        current_rank, current_weapon = current_rank

        # Peak xpower
        peak_xpower = (
            session.query(Player.x_power, Player.timestamp)
            .filter_by(id=player_id, mode=mode)
            .order_by(Player.x_power.desc())
            .first()
        )

        # Peak rank
        peak_rank = (
            session.query(Player.rank, Player.timestamp)
            .filter_by(id=player_id, mode=mode)
            .order_by(Player.rank.asc(), Player.timestamp.asc())
            .first()
        )

        # Time since they reached current xpower
        current_xpower = (
            session.query(Player.x_power)
            .filter_by(id=player_id, mode=mode)
            .order_by(Player.timestamp.desc())
            .first()[0]
        )

        peak_data.append(
            {
                "peak_xpower": {
                    "x_power": peak_xpower[0],
                    "timestamp": peak_xpower[1].strftime("%Y-%m-%d"),
                },
                "peak_rank": {
                    "rank": peak_rank[0],
                    "timestamp": peak_rank[1].strftime("%Y-%m-%d"),
                },
                "mode": mode,
                "current": {
                    "x_power": current_xpower,
                    "rank": current_rank,
                    "weapon": current_weapon,
                },
            }
        )

        latest_timestamp = max(
            max(x["timestamp"] for x in mode_data)
            for mode_data in modes_data.values()
        )
        now_date = dt.datetime.fromisoformat(latest_timestamp)

        seasons = get_seasons(now_date)

    session.close()

    return render_template(
        "player.html",
        player=player,
        modes_data=modes_data,
        aliases=aliases_data,
        peaks=peak_data,
        seasons=seasons,
    )


@app.route("/faq")
def faq():
    return render_template("faq.html")


if __name__ == "__main__":
    app.run(debug=True)
