from xml.dom import minidom
import json

doc = minidom.parse('bike-lane.svg')
path_strings = [
    path.getAttribute('d') for path in doc.getElementsByTagName('path')
]
# print(path_strings)

paths = []

for s in path_strings:
    assert s[0] == 'M', s
    # s = s[1:]
    i = 1
    points = []
    point = 'M'
    while True:
        if i >= len(s) or 'A' <= s[i] <= 'Z':
            # process point
            identifier = point[0]
            point = point[1:]
            if identifier == 'Z':
                points.append(points[0])
                break
            assert any(c in '0123456789. -' for c in point), point
            if identifier in 'ML':
                points.append([float(p) for p in point.split(' ')])
            elif identifier == 'V':
                assert ' ' not in point, point
                points.append([points[-1][0], float(point)])
                pass
            elif identifier == 'H':
                assert ' ' not in point, point
                points.append([float(point), points[-1][1]])
                pass
            else:
                raise Exception('Unknown identifier: ' + identifier)
            # print(points[-1])
            point = ''
        else:
            assert s[i] in '0123456789. -', s
        if i >= len(s):
            break
        point += s[i]
        i += 1
    paths.append(points)
    
doc.unlink()
print(paths)


names = ['east', 'west']

def bikelane(name):
    return 'bike-lane-' + name

polygons = []
for path, n in zip(paths, names):
    polygons.append({
        'id': bikelane(n),
        'polygon': f'POLYGON (({", ".join(f"{x} {y}" for x, y in path)}))'
    })

lanes = [ {'id': bikelane(n)} for n in names ]


with open('polygon.json', 'w') as f:
    json.dump(polygons, f, indent=2)
with open('lane.json', 'w') as f:
    json.dump(lanes, f, indent=2)


# intersection = paths[0]
# intersection_segment = paths[1]
# paths = paths[2:]
# assert len(paths) == 16
# lanes = paths[:8]
# lane_segment = paths[8:]

# DIRECTIONS = ['south', 'east', 'north', 'west']
# OUTINS = ['out', 'in']
# ids = []
# for d in DIRECTIONS:
#     for oi in OUTINS:
#         ids.append(d + '-' + oi)

# polygons = []
# intersections = []
# segments = []

# intersections = [{'id': 'intersection_inter', 'road': 'intersection'}]
# segments.append({
#     'start': 'POINT ()',
#     'end': 'POINT ()',
#     'heading': 0,
#     'polygonId': 'intersection',
# })