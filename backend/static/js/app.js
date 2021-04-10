const {createApp} = Vue
const {createRouter, createWebHistory} = VueRouter
const {createStore} = Vuex


const app = createApp({
    el:"#app",
    delimiters: ["[[", "]]"],
    data(){return{
        test: "TEST"
    }}
})
app.mount("#app")