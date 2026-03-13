import random
from datetime import date
from planner.models import ForestTree


MAX_TREES = 33

# --------------------------------
# TREE SPECIES POOLS
# --------------------------------

TREE_SPECIES = {

    "healthy": ["oak", "maple", "neem", "pine"],

    "rare": ["cherry_blossom", "jacaranda", "silver_birch"],

    "epic": ["redwood", "baobab", "dragon_tree"],

    "legendary": ["giant_sequoia", "methuselah_pine", "rainbow_eucalyptus"],

    "mythic": ["yggdrasil", "kalpavriksha", "world_tree"]

}

def determine_tree_status(user):
    """
    Determine tree tier based on current streak.
    """
    streak = user.userprofile.current_streak

    if streak >= 9:
        return "legendary"
    elif streak >= 7:
        return "epic"
    elif streak >= 5:
        return "rare"
    else:
        return "healthy"


def assign_depth_layer():
    """
    Weighted depth distribution.
    """
    return random.choices(
        population=[1, 2, 3],
        weights=[0.4, 0.35, 0.25],
        k=1
    )[0]

def choose_species(status):
    """
    Select species from the rarity pool.
    """
    pool = TREE_SPECIES.get(status, ["oak"])
    return random.choice(pool)

def prune_forest_if_needed(user):
    """
    If forest exceeds limit, prune oldest tree.
    Epic/Legendary may be saved to inventory.
    """

    from planner.models import UserInventoryTree

    trees = ForestTree.objects.filter(user=user).order_by("planted_date")

    if trees.count() < MAX_TREES:
        return

    profile = user.userprofile

    for tree in trees:

        # Mythic never pruned
        if tree.status == "mythic":
            continue

        # Healthy, Rare, Cut, Dry → delete
        if tree.status in ["healthy", "rare", "cut", "dry"]:
            tree.delete()
            return

        # Epic
        if tree.status == "epic":
            if profile.save_epic:
                inventory, _ = UserInventoryTree.objects.get_or_create(
                    user=user,
                    tree_type="epic"
                )
                inventory.quantity += 1
                inventory.total_earned += 1
                inventory.save()
            tree.delete()
            return

        # Legendary
        if tree.status == "legendary":
            if profile.save_legendary:
                inventory, _ = UserInventoryTree.objects.get_or_create(
                    user=user,
                    tree_type="legendary"
                )
                inventory.quantity += 1
                inventory.total_earned += 1
                inventory.save()
            tree.delete()
            return


def plant_tree(user):
    """
    Plant new tree after productive day.
    """

    prune_forest_if_needed(user)

    status = determine_tree_status(user)
    species = choose_species(status)
    
    new_tree = ForestTree.objects.create(
        user=user,
        planted_date=date.today(),
        status=status,
        species=species,
        tree_type=status,
        pos_x=round(random.uniform(0, 100), 2),
        pos_y=round(random.uniform(0, 100), 2),
        depth_layer=assign_depth_layer(),
        growth_stage=0,
        is_protected=(status == "mythic")
    )

    return {
        "status": "tree_planted",
        "tree_status": status,
        "tree_id": new_tree.id
    }