const {createApp} = Vue
const {createRouter, createWebHistory} = VueRouter
const {createStore} = Vuex

const store = createStore({
    state(){return{
        currentUser: null,
        status: "done"
    }},
    getters: {
        user: (state) => state.currentUser,
        status: (state) => state.status,
        isAuth: (state) => state.currentUser?true:false,
    },
    mutations: {
        login(state, user){
            state.currentUser = user;
        },
        logout(state){
            state.currentUser = null;
        },
        status(state, value){
            state.status = value;
        }
    },
    actions: {
        login({commit}){
            commit("status", "loading")
            return new Promise ((resolve, reject) => {
                axios.get("/api/current-user/")
                .then(response => {
                    commit("login", response.data);
                    commit("status", "done")
                    resolve(response.data)
                })
                .catch(error => {
                    reject(error.response)
                })
            })
        },
        getAllUsers({commit}){
            return new Promise((resolve, reject) =>{
                axios.get("/api/users/")
                .then(response => {
                    console.log("getAllUsers", response)
                    resolve(response)
                })
                .catch(error => {
                    reject(error.response)
                })
            })
        }
    }
})

const Home = {
    template: `
    <div>
        <div v-if="status === 'done'">
            <div v-for="_user in users" :key="user.id" style="border: 1px solid black">
                {{user}}
            </div>
        </div>
        <div v-else>Loading</div>
    </div>
    `,
    data(){return{
        users:[],
        errors:[],
    }},
    computed:{
        user(){return this.$store.getters.user},
        status(){return this.$store.getters.status;},
    },
    created(){
        this.$store.dispatch("getAllUsers").then(response => {
            this.users = response.data;
        })
    }
}

const app = createApp({
    el:"#app",
    delimiters: ["[[", "]]"],
    data(){return{
        test: "TEST"
    }},
    computed:{
        user() {return this.$store.getters.user;},
        status(){return this.$store.getters.status;},
    },
    created(){
        // this.$store.dispatch("login")
    }
})
const routes = [
    { path: '/', component: Home },
  ]
const router = createRouter({
    routes,
    history: createWebHistory(),
})
router.beforeEach(async (to, from, next) => {
    /* If not login push to register or login? */
    store.dispatch("login").then(user => {
        console.log(user)
        return next()
    })
    .catch(error => {
        next()
        location.href = window.location.protocol + "//" + window.location.host + "/accounts/login/"
    })
    next()
})


app.use(router)
app.use(store)
app.mount("#app")