const {createApp} = Vue
const {createRouter, createWebHistory} = VueRouter
const {createStore} = Vuex

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

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
        },
        getCurrentChats({commit}){
            return new Promise((resolve, reject) => {
                axios.get("/api/users/current_chats/")
                .then(response => {
                    console.log("getCurrentChats", response)
                    resolve(response)
                })
                .catch(error => {
                    reject(error.response)
                })
            })
        },
        getUserContacts({commit}){
            return new Promise((resolve, reject)=>{
                axios.get("/api/users/contacts/")
                .then(response => {
                    console.log("getUserContacts", response)
                    resolve(response)
                })
                .catch(error => reject(error.response))
            })
        },
    }
})

const ContactPage = {
    template: `
    <div>
        <h3>Contacts page</h3>
        <div v-for="user in users" :key="user.id" style="border: 1px solid black">
        {{user}}
        <button @click="createChat(user)">Chat with him</button>
        </div>
    </div>
    `, 
    data(){return{
        users:[],
    }},
    methods:{
        createChat(user){
            const data = {
                members: [user.id, this.currentUser.id],
            }
            axios.post("/api/chats/create_chat_with/", data, {headers: {"X-CSRFToken":readCookie("csrftoken") }})
            .then(response => {
                console.log(response);
                this.$router.push({name:"ChatPage", params:{id:response.data.id}})
            })
            .catch(error => {
                console.log(error.response)
                alert(error.response.data.errors)
            })
        },
    },
    computed: {
        currentUser(){return this.$store.getters.user;},
    },
    created(){
        this.$store.dispatch("getUserContacts")
        .then(response => {
            this.users = response.data
        })
    }
}

const ListChatPage = {
    template: `
    <div>
        <div v-if="status === 'done'">
            <h3>Chats Page</h3>
            <div v-for="chat in chats" :key="chat.id" style="border: 1px solid black">
                {{chat}}
            </div>
        </div>
        <div v-else>Loading</div>
    </div>
    `,
    data(){return{
        users:[],
        chats: [],
        errors:[],
    }},
    computed:{
        currentUser(){return this.$store.getters.user},
        status(){return this.$store.getters.status;},
    },
    created(){
        this.$store.dispatch("getAllUsers").then(response => {
            this.users = response.data;
            this.$store.dispatch("getCurrentChats").then(response => {
                this.chats = response.data;
            })
        })
    }
}

const ChatPage = {
    template: `
        <div>{{id}}
            <div v-for="member in members" :key="member.id" style="border: 1px solid red">
                {{member.username}}
            </div>
            <div v-for="message in messages" :key="message.id" style="border: 1px solid black">
                {{message.user.username}}: {{message.text}}
            </div>
        </div>
    `,
    data(){return{
        messages: [],
        members: [],
        chat:[],
    }},
    computed: {
        id(){return this.$route.params.id;}
    },
    methods:{
        getMessages(){
            return new Promise((resolve, reject) => {
                axios.get(`/api/messages/messages_in_chat/?chat_id=${this.id}`)
                .then(response => {
                    console.log(response)
                    resolve(response)
                })
                .catch(error => {
                    console.log(error.response)
                    reject(error.response)
                })
            })
        },
        getChat(){
            return new Promise((resolve, reject)=>{
                axios.get(`/api/chats/${this.id}/`)
                .then(response => {
                    resolve(response)
                })
                .catch(error=>{
                    reject(error.response)
                })
            })
        },
    },
    created(){
        // this.getMessages()
        Promise.all([this.getChat(), this.getMessages()])
        .then(([chat_response, message_response]) => {
            console.log("values", chat_response, message_response)
            this.chat = chat_response.data;
            this.messages = message_response.data.results;
            this.members = chat_response.data.members;
        })
        .catch(([chat_error, message_error]) => {
            console.log(error)
        })
    },
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
        // axios.defaults.headers.common["HTTP_X_XSRF_TOKEN"] = readCookie("csrftoken")
    }
})

const routes = [
    { path: '/', name:"ListChatPage", component: ListChatPage },
    { path: '/contacts', name:"ContactPage", component: ContactPage },
    { path: '/chat/:id', name:"ChatPage", component: ChatPage },
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