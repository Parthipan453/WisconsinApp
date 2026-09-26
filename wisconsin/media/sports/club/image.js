let  images=[ "https://picsum.photos/id/1015/600/300",
    "https://picsum.photos/id/1016/600/300",
    "https://picsum.photos/id/1019/600/300",
    "https://picsum.photos/id/1018/600/300"
]
let index=0
let img=document.getElementById('img')
img.src=images[index]

 function next(){
    index++
    if(index >=images.length){
        index=0
    }
    img.src=images[index]

 }
 function prev(){
    index--
    if(index<0){
        index=images.length -1
    }
    img.src=images[index]
 }
 document.getElementById('next').addEventListener('click', next)
 document.getElementById('prev').addEventListener('click', prev)