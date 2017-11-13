class CodeTableException(Exception):
    """
    Exception while validating the code tables
    """


codetables = ["ct_acidity", "ct_soil_mlw_class", "ct_soil_codes",
                "lnk_acidity", "ct_seepage", "ct_vegetation", "ct_management",
                "ct_nutrient_level", "ct_mineralisation"]


def check_lower_upper_boundaries(df, min_col, max_col, value):
    """Checks whether there are no overlaps between min_col and max_col

    Parameters
    ==========
    df: dataframe to check, must contain min_col and max_col
    min_col, max_col: columns containing the mni and max value
    value: the column containing the reclassified value

    This function will check if there are no overlapping values when
    classifying the dataframe (df).
    """

    group_cols = set(df.columns.tolist()) - {min_col, max_col, value}
    for sel_group, subtable in df.groupby(list(group_cols)):
        min_values = subtable[min_col]
        max_values = subtable[max_col]
        for (i, index) in enumerate(min_values.index):
            if i > 0:
                if(min_values[index] != max_values[prev_index]):
                    raise CodeTableException(
                        "Min and max values in table do not correspond"
                    )
            prev_index = index

def check_inner_join(df1, df2, f1, f2=None):
    if f2 is None:
        f2 = f1
    u2 = df2[f2].unique().sort()
    u1 = df1[f1].unique().sort()
    if u1 != u2:
        print(u1)
        print(u2)
        raise CodeTableException(
            "Different keys exist in tables.")


def check_unique(df, col):
    u = df[col].unique()
    if u.size != df[col].size:
        raise CodeTableException(
            "Non unique fields in column {}".format(col))


def validate_tables_acidity(ct_acidity, ct_soil_mlw_class,
                            ct_soil_codes, lnk_acidity, ct_seepage):

    # check tables
    check_unique(ct_soil_codes, "soil_code")
    check_unique(ct_soil_codes, "soil_name")

    check_unique(ct_acidity, "acidity")

    check_unique(ct_seepage, "seepage")
    check_lower_upper_boundaries(ct_seepage, "seepage_min", "seepage_max",
                                                    "seepage")

    # check links between tables
    check_inner_join(ct_acidity, lnk_acidity, "acidity")
    check_inner_join(ct_soil_codes, ct_soil_mlw_class,"soil_group")
    check_inner_join(ct_soil_mlw_class, lnk_acidity, "soil_mlw_class")
    check_inner_join(ct_seepage, lnk_acidity, "seepage")
