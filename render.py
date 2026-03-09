import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import forrender  # your generated python file
import matplotlib as mpl
import os
mpl.rcParams['animation.ffmpeg_path'] = f"{os.path.expanduser("~")}\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.0.1-full_build\\bin\\ffmpeg.exe"

instructions = forrender.instructions
div = 10
# Accumulate absolute positions
x = y = z = 0/div
xs = [x]
ys = [y]
zs = [z]

for dx, dy, dz in instructions:
    x += dx
    y += dy
    z += dz
    xs.append(x/div)
    ys.append(y/div)
    zs.append(z/div)

# Create 3D figure
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Path line + moving point
line, = ax.plot([], [], [], lw=2)
point, = ax.plot([], [], [], 'ro')

# Set axis limits so it doesn't autoscale every frame
ax.set_xlim(min(xs), max(xs))
ax.set_ylim(min(ys), max(ys))
ax.set_zlim(min(zs), max(zs))

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")

def update(i):
    line.set_data(xs[:i], ys[:i])
    line.set_3d_properties(zs[:i])

    point.set_data([xs[i]], [ys[i]])
    point.set_3d_properties([zs[i]])

    return line, point

ani = animation.FuncAnimation(fig, update, frames=len(xs), interval=1)
writervideo = animation.FFMpegWriter(fps=30)
ani.save('render.mp4', writer=writervideo)
plt.close()
