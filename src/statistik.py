from project import Project

project = Project("../data/TH913_3523")

print(project.design[0,0])

x0 = project.config["design"]["rx"]
y0 = project.config["design"]["ry"]

w = project.config["design"]["rw"]
h = project.config["design"]["rh"]

for x in range(x0,x0+w):
  n = 0
  
  for y in range(y0,y0+h):
    c1 = color = tuple(project.design[y%h, x].tolist())
    c2 = color = tuple(project.design[(y+1)%h, x].tolist())

    if c1 != c2: n += 1
    
  print(n)

