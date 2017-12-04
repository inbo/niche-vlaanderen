import rasterio
from pkg_resources import resource_filename

import pandas as pd
import numpy as np

from .spatial_context import SpatialContext


class FloodPlainError(Exception):
    """"""


class FloodPlain(object):
    def __init__(self, depths=None, duration=None, frequency=None,
                 lnk_potential=None, potential=None):
        self._ct = dict()
        self._veg = dict()

        for i in ["duration", "frequency", "lnk_potential", "potential"]:
            if locals()[i] is None:
                ct = resource_filename(
                        "niche_vlaanderen",
                        "system_tables/floodplains/"+i+".csv")
            else:
                ct = locals()[i]
            self._ct[i] = pd.read_csv(ct)

    def _calculate(self, depth, frequency, duration, period):
        orig_shape = depth.shape
        depth = depth.flatten()

        for veg_code, subtable_veg in \
                self._ct["lnk_potential"].groupby(["veg_code"]):
            subtable_veg = subtable_veg.reset_index()
            self._veg[veg_code] = np.zeros(depth.shape, dtype="uint8")
            groupby_cols = ["period", "frequency", "duration"]
            for index, subtable in subtable_veg.groupby(groupby_cols):
                if (period, frequency, duration) == index:
                    subtable.reset_index()
                    for row in subtable.itertuples():
                        veg = self._veg[veg_code]
                        veg[row.depth == depth] = row.potential
                        self._veg[veg_code] = np.maximum(veg,
                                                         self._veg[veg_code])
            self._veg[veg_code] = self._veg[veg_code].reshape(orig_shape)

    def calculate(self, depth_file, frequency, period, duration):
        with rasterio.open(depth_file) as dst:
            depth = dst.read(1)
            self._context = SpatialContext(dst)
        self._calculate(depth, frequency, duration, period)
        self.options = (frequency, duration, period)

    def show(self, key):
        plt = rasterio.plot.get_plt()
        import matplotlib.patches as mpatches
        from matplotlib.colors import Normalize

        if key not in self._veg.keys():
            print("vegetation type not modeled")
            return

        fig, ax = plt.subplots()
        ((a, b), (c, d)) = self._context.extent
        mpl_extent = (a, c, d, b)

        im = plt.imshow(self._veg[key], extent=mpl_extent,
                        norm=Normalize(0, 3))
        options = list(self.options)
        options[2] = "< 14 days" if self.options[2] == 1 else "> 14 days"
        ax.set_title("{} ({})".format(key, options))

        labels = self._ct["potential"]["description"]
        values = self._ct["potential"]["code"]

        colors = [im.cmap(value/(len(values) - 1)) for value in values]
        patches = [mpatches.Patch(color=colors[i],
                                  label=labels[i]) for i in values]
        plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2,
                   borderaxespad=0.)

        plt.show()

    def combine(self, niche_result):
        # check niche model has been run
        if not hasattr(niche_result, "_vegetation"):
            raise FloodPlainError(
                "Niche model must be run prior to running this module.")
