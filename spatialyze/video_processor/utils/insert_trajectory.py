import datetime
import numpy as np
import numpy.typing as npt

from ...database import Database
from ...utils import join
from ..types import Float3
from .infer_heading import infer_heading


def insert_trajectory(
    database: "Database",
    item_id: str,
    camera_id: str,
    object_type: str,
    postgres_timestamps: "list[datetime.datetime]",
    pairs: "list[npt.NDArray[np.floating]]",
    itemHeading_list: "list[float | None]",
    translation_list: "list[Float3]",
    # road_types: "list[str]",
    # roadpolygon_list: "list[list[tuple[float, float]]]"
):
    traj_centroids: "list[str]" = []
    translations: "list[str]" = []
    itemHeadings: "list[str]" = []
    prevTimestamp: "str | None" = None
    prevPoint: "Float3 | None" = None
    for timestamp, current_point, curItemHeading, current_trans in zip(
        postgres_timestamps, pairs, itemHeading_list, translation_list
    ):
        if prevTimestamp == timestamp:
            continue
        prevTimestamp = timestamp

        # Construct trajectory
        traj_centroids.append(f"POINT Z ({join(current_point, ' ')})@{timestamp}")
        translations.append(f"POINT Z ({join(current_point, ' ')})@{timestamp}")
        curItemHeading = infer_heading(curItemHeading, prevPoint, current_point)
        if curItemHeading is not None:
            itemHeadings.append(f"{curItemHeading}@{timestamp}")
        # roadTypes.append(f"{cur_road_type}@{timestamp}")
        # polygon_point = ', '.join(join(cur_point, ' ') for cur_point in list(
        #     zip(*cur_roadpolygon.exterior.coords.xy)))
        # roadPolygons.append(f"Polygon (({polygon_point}))@{timestamp}")
        prevPoint = current_point

    # Insert the item_trajectory separately
    item_headings = (
        f"tfloat 'Interp=Stepwise;{{[{', '.join(itemHeadings)}]}}'" if itemHeadings else "null"
    )
    insert_trajectory = f"""
    INSERT INTO Item_General_Trajectory (itemId, cameraId, objectType, trajCentroids,
    translations, itemHeadings)
    VALUES (
        '{item_id}',
        '{camera_id}',
        '{object_type}',
        tgeompoint '{{[{', '.join(traj_centroids)}]}}',
        tgeompoint '{{[{', '.join(translations)}]}}',
        {item_headings}
    );
    """

    database.execute(insert_trajectory)
    database._commit()
