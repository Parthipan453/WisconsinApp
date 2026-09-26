let button = document.getElementById("add")
let todoList = document.getElementById("todoList")
let input = document.getElementById("input")

// let todoArr = []
// local storage
    let todoArr=JSON.parse(localStorage.getItem('todoArr')) || []
window.onload=()=>{
    todoArr.forEach(todo=> todoDisplay(todo))
}
// add btn
button.addEventListener('click', () => {
    if(input.value==""){
        return
    }
    todoArr.push(input.value)
      // entire array store in string format
    localStorage.setItem('todoArr',JSON.stringify(todoArr))
     console.log(todoArr)
    todoDisplay(input.value)
    input.value = ""
})

// displaytodo
function todoDisplay(todo) {
    let para = document.createElement('p')
    para.style.cursor = 'pointer'
    para.innerText = todo
    todoList.appendChild(para)

    para.addEventListener('click', () => {
        para.style.textDecoration = 'line-through'
        remove(todo)
    })
    para.addEventListener('dblclick', () => {
        todoList.removeChild(para)
        remove(todo)
    })
}
function remove(todo) {
    let index = todoArr.indexOf(todo)
    if (index > -1) {
          todoArr.splice(index, 1)
    }
      
    
}
