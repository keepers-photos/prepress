def generate_pod_package_id(cover_type, size_type, page_count):
    """
    Generate the pod_package_id for the given cover type and size.

    :param cover_type: 'hard_cover' or 'soft_cover'
    :param size_type: 'small_square' or 'square'
    :param page_count: number of pages in the book
    :return: 27-character pod_package_id
    """
    # Define the components of the pod_package_id
    trim_size = "0750X0750" if size_type == "small_square" else "0850X0850"
    color = "FC"  # Full color
    print_quality = "PRE" # Premium print quality
    bind = (
        "CW" if cover_type == "hard_cover" else "PB"
    )  # Case wrap for hardcover, Perfect binding for softcover
    paper = "080CW444"  # 80# coated white paper with a bulk of 444 ppi
    finish = "M"  # Matte cover coating
    linen = "X"  # No linen (for softcover)
    foil = "X"  # No foil

    # Combine all components
    pod_package_id = (
        f"{trim_size}{color}{print_quality}{bind}{paper}{finish}{linen}{foil}"
    )

    return pod_package_id
