from planner.models import ForestTree
from planner.services.leaderboard_engine import build_leaderboard
import random

MYTHIC_SPECIES = [
    "yggdrasil",
    "kalpavriksha",
    "world_tree"
]


def check_and_update_mythic(user):
    """
    Grant or downgrade mythic tree based on Top 3 all-time leaderboard.
    """

    leaderboard = build_leaderboard(metric="points", mode="all_time")

    # Find user rank
    rank = None
    for index, entry in enumerate(leaderboard):
        if entry["username"] == user.username:
            rank = index + 1
            break

    has_mythic = ForestTree.objects.filter(
        user=user,
        status="mythic"
    ).exists()

    # 🟢 GRANT MYTHIC
    if rank and rank <= 3:
        if not has_mythic:
            ForestTree.objects.create(
                user=user,
                status="mythic",
                species=random.choice(MYTHIC_SPECIES),
                tree_type="mythic",
                pos_x=random.uniform(40, 60),   # ✅ FIXED
                pos_y=random.uniform(40, 60),
                depth_layer=1,
                growth_stage=3,
                is_protected=False
            )
            return {"status": "mythic_granted", "rank": rank}

        return {"status": "mythic_retained", "rank": rank}

    # 🔴 DOWNGRADE (NOT DELETE)
    else:
        if has_mythic:
            ForestTree.objects.filter(
                user=user,
                status="mythic"
            ).update(status="legendary")

            return {"status": "mythic_downgraded", "rank": rank}

    return {"status": "no_mythic_change", "rank": rank}