# CatSlicer: Minimal STL → Movement Instructions
import numpy as np
from stl import mesh
import sys

steps_per_mm = 80
layer_height = 0.2

def intersect_triangle_with_plane(tri, z, eps=1e-6):
    pts = []
    for a, b in [(0,1), (1,2), (2,0)]:
        p1 = tri[a]
        p2 = tri[b]

        z1 = p1[2] - z
        z2 = p2[2] - z

        # If both endpoints are extremely close to the plane, skip the edge
        if abs(z1) < eps and abs(z2) < eps:
            continue

        # If one endpoint is almost on the plane, snap it
        if abs(z1) < eps:
            pts.append((p1[0], p1[1]))
            continue
        if abs(z2) < eps:
            pts.append((p2[0], p2[1]))
            continue

        # Proper crossing
        if z1 * z2 < 0:
            t = z1 / (z1 - z2)
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            pts.append((x, y))

    # Keep only 2 points max
    if len(pts) > 2:
        pts = pts[:2]

    return pts

def generate_infill(path, spacing=1.0):
    # Flatten path into list of points
    pts = [p[0] for p in path] + [path[-1][1]]

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    min_y = min(ys)
    max_y = max(ys)

    infill_segments = []

    y = min_y
    while y <= max_y:
        # Find intersections of horizontal line with polygon edges
        intersections = []
        for i in range(len(pts)-1):
            x1, y1 = pts[i]
            x2, y2 = pts[i+1]

            if (y1 - y) * (y2 - y) < 0:  # crosses the scanline
                t = (y - y1) / (y2 - y1)
                x = x1 + t * (x2 - x1)
                intersections.append(x)

        intersections.sort()

        # Pair up intersections into fill lines
        for i in range(0, len(intersections), 2):
            if i+1 < len(intersections):
                x_start = intersections[i]
                x_end = intersections[i+1]
                infill_segments.append(((x_start, y), (x_end, y)))

        y += spacing

    return infill_segments

def slice_mesh(stl_mesh):
    z_vals = stl_mesh.vectors[:,:,2].flatten()
    min_z, max_z = np.min(z_vals), np.max(z_vals)

    # Normalize so model starts at Z = 0
    stl_mesh.vectors[:,:,2] -= min_z
    max_z = max_z - min_z

    num_layers = int(np.floor(max_z / layer_height)) + 1

    layers = {}

    for i in range(num_layers):
        z = i * layer_height
        segments = []

        for tri in stl_mesh.vectors:
            pts = intersect_triangle_with_plane(tri, z)
            if len(pts) == 2:
                segments.append(pts)

        layers[i] = segments

    return layers

def close(a, b, eps=1e-5):
    return abs(a[0]-b[0]) < eps and abs(a[1]-b[1]) < eps

def sort_segments(segments):
    paths = []
    segments = segments.copy()

    while segments:
        seg = segments.pop(0)
        path = [seg]

        changed = True
        while changed:
            changed = False
            for s in segments:
                if close(s[0], path[-1][1]):
                    path.append(s)
                    segments.remove(s)
                    changed = True
                    break
                if close(s[1], path[-1][1]):
                    path.append((s[1], s[0]))
                    segments.remove(s)
                    changed = True
                    break

        paths.append(path)

    return paths

def mm_to_steps(dx, dy, dz):
    return int(dx * steps_per_mm), int(dy * steps_per_mm), int(dz * steps_per_mm)

def generate_instructions(layers):
    instructions = []
    current_x = 0
    current_y = 0
    current_z = 0

    for i, segments in layers.items():
        if not segments:
            continue

        paths = sort_segments(segments)

        for path in paths:
            for (x1, y1), (x2, y2) in path:

                # 1. Move to the start of the segment (absolute → relative)
                dx = x1 - current_x
                dy = y1 - current_y
                instructions.append(mm_to_steps(dx, dy, 0))

                current_x = x1
                current_y = y1

                # 2. Draw the segment
                dx = x2 - x1
                dy = y2 - y1
                instructions.append(mm_to_steps(dx, dy, 0))

                current_x = x2
                current_y = y2


            # 2. Infill
            infill = generate_infill(path)
            for (x1, y1), (x2, y2) in infill:
                # 1. Move to the start of the segment (absolute → relative)
                dx = x1 - current_x
                dy = y1 - current_y
                instructions.append(mm_to_steps(dx, dy, 0))

                current_x = x1
                current_y = y1

                # 2. Draw the segment
                dx = x2 - x1
                dy = y2 - y1
                instructions.append(mm_to_steps(dx, dy, 0))

                current_x = x2
                current_y = y2

        # Move up one layer
        dz = layer_height
        instructions.append((0, 0, int(dz * steps_per_mm)))
        current_z += dz

    return instructions

# Load STL
your_mesh = mesh.Mesh.from_file("temp.stl")

# Slice
layers = slice_mesh(your_mesh)
def compress_instructions(instr):
    compressed = []
    last = None

    for x, y, z in instr:
        # Skip useless moves
        if x == 0 and y == 0 and z == 0:
            continue

        if last is None:
            last = [x, y, z]
            continue

        lx, ly, lz = last

        # Merge X-only moves
        if y == 0 and z == 0 and ly == 0 and lz == 0:
            last[0] += x
            continue

        # Merge Y-only moves
        if x == 0 and z == 0 and lx == 0 and lz == 0:
            last[1] += y
            continue

        # Merge Z-only moves
        if x == 0 and y == 0 and lx == 0 and ly == 0:
            last[2] += z
            continue

        # Otherwise, push last and start new
        compressed.append(tuple(last))
        last = [x, y, z]

    # Push final
    if last is not None:
        compressed.append(tuple(last))

    return compressed
# Convert to movement
instructions = generate_instructions(layers)
instructions = compress_instructions(instructions)

# Output for Arduino
oldstdout = sys.stdout
sys.stdout = open("flashme.ino", "w")
print("""#include <avr/pgmspace.h>
#define am1  13
#define ap1  12
#define bp1  11
#define bm1  10
#define am2   9
#define ap2   8
#define bp2   7
#define bm2   6
#define am3   5
#define ap3   4
#define bp3   3
#define bm3   2
int slowness = 0;""")
print("const int instructions[][3] PROGMEM = {")
for x, y, z in instructions:
    print(f"  {{{x}, {y}, {z}}},")
print("};")
print(r"""
void setup() {
  pinMode(am1, OUTPUT);
  pinMode(ap1, OUTPUT);
  pinMode(bp1, OUTPUT);
  pinMode(bm1, OUTPUT);
  pinMode(am2, OUTPUT);
  pinMode(ap2, OUTPUT);
  pinMode(bp2, OUTPUT);
  pinMode(bm2, OUTPUT);
  pinMode(am3, OUTPUT);
  pinMode(ap3, OUTPUT);
  pinMode(bp3, OUTPUT);
  pinMode(bm3, OUTPUT);
}
int len() {
  return sizeof(instructions)/sizeof(instructions[0]);
}
void loop() {
  parse(instructions, len());
  for(;;){ }
}
void parse(const int instructions[][3], int count) {
  for (int i = 0; i < count; i++) {
    int x = pgm_read_word(&instructions[i][0]);
    int y = pgm_read_word(&instructions[i][1]);
    int z = pgm_read_word(&instructions[i][2]);
    move(x, y, z);
  }
}
void move(int x, int y, int z) {
  x = -x;
  y = -y;
  z = -z;
  if (x > 0) {
    for (int i = 0; i < x; i++) stepf(am1, ap1, bp1, bm1);
  } else {
    for (int i = 0; i > x; i--) stepb(am1, ap1, bp1, bm1);
  }
  if (y > 0) {
    for (int j = 0; j < y; j++) stepf(am2, ap2, bp2, bm2);
  } else {
    for (int j = 0; j > y; j--) stepb(am2, ap2, bp2, bm2);
  }
  if (z > 0) {
    for (int k = 0; k < z; k++) stepf(am3, ap3, bp3, bm3);
  } else {
    for (int k = 0; k > z; k--) stepb(am3, ap3, bp3, bm3);
  }
}
void stop(int am, int ap, int bp, int bm) {
  digitalWrite(am, LOW);
  digitalWrite(ap, LOW);
  digitalWrite(bp, LOW);
  digitalWrite(bm, LOW);
}
void stepf(int am, int ap, int bp, int bm) {
  digitalWrite(ap, HIGH); digitalWrite(am, LOW);  digitalWrite(bp, LOW);  digitalWrite(bm, HIGH); delay(slowness);
  digitalWrite(ap, LOW);  digitalWrite(am, HIGH); digitalWrite(bp, LOW);  digitalWrite(bm, HIGH); delay(slowness);
  digitalWrite(ap, LOW);  digitalWrite(am, HIGH); digitalWrite(bp, HIGH); digitalWrite(bm, LOW);  delay(slowness);
  digitalWrite(ap, HIGH); digitalWrite(am, LOW);  digitalWrite(bp, HIGH); digitalWrite(bm, LOW);  delay(slowness);
}
void stepb(int am, int ap, int bp, int bm) {
  digitalWrite(ap, HIGH); digitalWrite(am, LOW);  digitalWrite(bp, HIGH); digitalWrite(bm, LOW);  delay(slowness);
  digitalWrite(ap, LOW);  digitalWrite(am, HIGH); digitalWrite(bp, HIGH); digitalWrite(bm, LOW);  delay(slowness);
  digitalWrite(ap, LOW);  digitalWrite(am, HIGH); digitalWrite(bp, LOW);  digitalWrite(bm, HIGH); delay(slowness);
  digitalWrite(ap, HIGH); digitalWrite(am, LOW);  digitalWrite(bp, LOW);  digitalWrite(bm, HIGH); delay(slowness);
}
""")
sys.stdout.close()
sys.stdout = oldstdout

with open("forrender.py", "w") as f:
    f.write("instructions = [")
    for x, y, z in instructions:
        f.write(f"[{x}, {y}, {z}],")
    f.write("]")
def compute_time(instructions, slowness=0.2):
    time_per_step = 4 * slowness / 1000.0  # seconds
    total_steps = 0

    for x, y, z in instructions:
        total_steps += abs(x) + abs(y) + abs(z)

    total_time_sec = total_steps * time_per_step
    return total_time_sec

time = compute_time(instructions)

# Raw prints
print("Total time (sec):", time)
print("Total time (min):", time / 60)
print("Total time (hrs):", time / 3600)

# Format nicely
if time < 60:
    # Less than 1 minute
    times = f"{int(time)}s"

elif time < 3600:
    # Less than 1 hour
    minutes = int(time // 60)
    seconds = int(time % 60)
    if seconds > 0:
        times = f"{minutes}m{seconds}s"
    else:
        times = f"{minutes}m"

else:
    # 1 hour or more
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    if minutes > 0:
        times = f"{hours}h {minutes}m"
    else:
        times = f"{hours}h"

with open("temp.txt", "w") as f:
    f.write(times)