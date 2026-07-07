# 打包docker

`./docker-build.sh v1.0.0`

# 查看docker

`docker images`

# 导出

`docker save -o ~/study/ctod/ctod:v1.0.0.tar ctod:v1.0.0`

# 删除

`docker rmi id`
`docker rmi -f id`

# 服务器依赖目录 /mnt/glusterfs/rscb

# 服务器缓存目录 /mnt/glusterfs/rscb/dem-terrain/

# k8s部署启动命令

`docker run -p 5000:5000 -v /mnt/glusterfs/rscb/dem-terrain:/cache -v /mnt/glusterfs/rscb:/mnt/glusterfs/rscb ctod:v1.0.0 --port 5000 --tile-cache-path /cache --unsafe`
