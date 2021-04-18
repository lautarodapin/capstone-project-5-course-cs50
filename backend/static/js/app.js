const { createApp } = Vue
const { createRouter, createWebHistory } = VueRouter
const { createStore } = Vuex

const ws_schema = window.location.protocol === "http:" ? "ws:" : "wss:";
const host = window.location.host;
const ws_path = ws_schema + "//" + host + "/ws/";

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}


const store = createStore({
    state() {
        return {
            currentUser: null,
            status: "done",
            ws: null,
        }
    },
    getters: {
        user: (state) => state.currentUser,
        status: (state) => state.status,
        isAuth: (state) => state.currentUser ? true : false,
        wsConnected(state){return state != null && state.ws.readyState === 1? true : false} // TODO this isnt updating in the computed values
    },
    mutations: {
        login(state, user) {
            state.currentUser = user;
        },
        logout(state) {
            state.currentUser = null;
        },
        status(state, value) {
            state.status = value;
        },
        createWs(state) {
            state.ws = new WebSocket(ws_path)
        },
    },
    actions: {
        login({ commit }) {
            commit("status", "loading")
            return new Promise((resolve, reject) => {
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
        createWs({ commit, state, dispatch}){
            console.log("Dispatching creating ws")
            commit("createWs")
            state.ws.onmessage = function(e){
                console.log(JSON.stringify(e.data))
            }
            state.ws.onclose = function(e){
                console.log(e);
                setTimeout(function(){dispatch("createWs")}, 1000 * 10);
            }
            state.ws.onerror = function(e){
                console.log(e);
                state.ws.close();
            }
        },
        getAllUsers({ commit }) {
            return new Promise((resolve, reject) => {
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
        getCurrentChats({ commit }) {
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
        getUserContacts({ commit }) {
            return new Promise((resolve, reject) => {
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



const MessageForm = {
    template: `
    <form @submit.prevent="submitForm" class="row mt-2">
        <div class="col">
            <input v-model="message" type="text" class="form-control" placeholder="Type a message . . . " />
        </div>
        <div class="col-auto">
            <button class="btn btn-info float-end rounded-pill border-1" type="submit">Send</button>
        </div>
    </form>
    `,
    emits: ["submitForm"],
    data() {
        return {
            message: "",
        }
    },
    methods: {
        submitForm() {
            this.$emit("submitForm", this.message)
            this.message = ""
        }
    }
}


const MessageIncoming = {
    // <div class="incoming_msg_img"> <img src="https://ptetutorials.com/images/user-profile.png" alt="sunil">
    // </div>
    template: `
    <div class="alert alert-dark me-5 p-0">
        <p class="ps-2 pt-1 pb-1 mb-0">{{message.text}}</p>
        <small class="text-muted p-0 ps-2 m-0">{{message.created_at}}</small>
    </div>
    `,
    props:["message"],
}
const MessageOutgoing = {
    template: `
    <div class="alert alert-info ms-5 p-0">
        <p class="pe-2 pt-1 pb-1 mb-0">{{message.text}}</p>
        <small class="text-muted p-0 pe-2 m-0">{{message.created_at}}</small>
    </div>
    `,
    props:["message"],
}


const ChatPaper = {
    template: `
    <div>
        <div v-if="status == 'done'" class="container-sm">
            <div class="row overflow-auto" style="height: 80vh;">
                <div 
                    v-for="message in messages"
                    :class="message.user.id == currentUser.id? 
                        'col-12 text-end     pe-5' : 
                        'col-12 text-start   ps-5'"
                >
                    <MessageOutgoing class="" v-if="message.user.id == currentUser.id" :message="message" />
                    <MessageIncoming class="" v-else :message="message" />
                </div>
                <div id="scrollBottom"></div>
            </div>
            <MessageForm @submitForm="createMessage" style="height: 10vh"/>
        </div>
        <div v-else class="container-sm text-center">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    </div>
    `,
    components: {MessageIncoming, MessageOutgoing, MessageForm,},
    props:["messages"],
    emits:["createMessage"],
    computed:{
        currentUser(){return this.$store.getters.user;},
        status() { return this.$store.getters.status; },
    },
    methods:{
        scrollBottom(){
            var el = document.getElementById("scrollBottom")
            if (el) el.scrollIntoView({behavior: 'smooth'});
        },
        createMessage(message){
            this.$emit("createMessage", message)
            this.scrollBottom()
        },
    },
    updated(){
        this.$nextTick(() => this.scrollBottom()) ;
    }

}

const ContactPage = {
    template: `
    <div>
        <div v-if="status === 'done'" class="container-sm">
            <h3 class="display-6">Contacts page</h3>
            <div 
                v-for="user in users" :key="user.id" 
                @click="createChat(user)" 
                class="card mb-2"
            >
                <div class="card-body">
                    {{user.username}}
                    <small class="text-muted">
                        {{user.last_login}}
                    </small>
                </div>
            </div>
        </div>
        <div v-else class="container-sm text-center">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            users: [],
        }
    },
    methods: {
        createChat(user) {
            const data = {
                members: [user.id, this.currentUser.id],
            }
            axios.post("/api/chats/create_chat_with/", data, { headers: { "X-CSRFToken": readCookie("csrftoken") } })
                .then(response => {
                    console.log(response);
                    this.$router.push({ name: "ChatPage", params: { id: response.data.id } })
                })
                .catch(error => {
                    console.log(error.response)
                    alert(error.response.data.errors)
                })
        },
    },
    computed: {
        currentUser() { return this.$store.getters.user; },
        status() { return this.$store.getters.status; },
    },
    created() {
        this.$store.dispatch("getUserContacts")
            .then(response => {
                this.users = response.data
            })
    }
}

const ListChatPage = {
    template: `
        <div class="container-sm">
            <h3 class="display-6">Chats Page</h3>
            {{wsConnected}}
            <div v-for="chat in chats" :key="chat.id" @click="openChat(chat)" class="card mb-1">
                <div class="card-body">
                    {{otherMember(chat).username}}
                    <small class="text-muted">
                        {{getLastChatMessage(chat).text}}
                    </small>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            users: [],
            chats: [],
            errors: [],
        }
    },
    methods: {
        openChat(chat) {
            this.$router.push({ name: "ChatPage", params: { id: chat.id } })
        },
        otherMember(chat){
            var other = chat.members.filter(member => member.id != this.currentUser.id);
            return other[0]
        },
        getLastChatMessage(chat){
            return chat.messages[chat.messages.length - 1]
        }
    },
    computed: {
        currentUser() { return this.$store.getters.user },
        status() { return this.$store.getters.status; },
        wsConnected() { return this.$store.state.ws.readyState;},
    },
    created() {
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
        <div>
            <div v-if="status === 'done'" class="alert">
                <ChatPaper :messages="messages" @createMessage="createMessage"/>
            </div>
            <div v-else class="container-sm text-center">
                <div class="spinner-border text-success" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        </div>
    `,
    components: { MessageForm, ChatPaper },
    data() {
        return {
            messages: [],
            members: [],
            chat: [],
            ws: null,
        }
    },
    computed: {
        id() { return this.$route.params.id; },
        currentUser() { return this.$store.getters.user; },
        status() { return this.$store.getters.status; },
    },
    methods: {
        scrollBottom(){
            var el = document.getElementById("scrollBottom")
            if (el) el.scrollIntoView({behavior: 'smooth'});
        },
        createMessage(message) {
            console.log(message)
            const data = {
                type: "chat_message",
                user: this.currentUser.id,
                message: message,
            }
            this.ws.send(JSON.stringify(data))
        },
        createWebsocket() {
            self = this;
            this.ws = new WebSocket(`${ws_schema}//${host}/ws/chat/${this.id}/`)
            this.ws.onmessage = function (response) {
                const data = JSON.parse(response.data)
                console.log(response, data)
                switch (data.type) {
                    case "chat_message":
                        self.messages.push(data.data)
                        self.scrollBottom();
                        break;
                    case "notification":
                        console.log("notification", data)
                        break;
                    default:
                        break;
                }
            }
            this.onclose = function (e) {
                console.log(e)
                setTimeout(function () { self.createWebsocket; }, 1000 * 10);
            }
            this.onerror = function (e) {
                console.log(e)
                self.ws.close();
            }
        },
        getMessages() {
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
        getChat() {
            return new Promise((resolve, reject) => {
                axios.get(`/api/chats/${this.id}/`)
                    .then(response => {
                        resolve(response)
                    })
                    .catch(error => {
                        reject(error.response)
                    })
            })
        },
    },
    created() {
        this.$store.commit("status", "loading")
        Promise.all([this.getChat(), this.getMessages()])
            .then(([chat_response, message_response]) => {
                console.log("values", chat_response, message_response)
                this.chat = chat_response.data;
                this.messages = message_response.data.results;
                this.members = chat_response.data.members;
                this.$store.commit("status", "done")

            })
            .catch(([chat_error, message_error]) => {
                console.log(error)
            })
        this.createWebsocket();
    },
    mounted(){
        this.scrollBottom();
    }
}

const app = createApp({
    el: "#app",
    delimiters: ["[[", "]]"],
    data() {
        return {
            test: "TEST"
        }
    },
    computed: {
        user() { return this.$store.getters.user; },
        status() { return this.$store.getters.status; },
    },
    created() {
        this.$store.dispatch("createWs")
    }
})

const routes = [
    { path: '/', name: "ListChatPage", component: ListChatPage },
    { path: '/contacts', name: "ContactPage", component: ContactPage },
    { path: '/chat/:id', name: "ChatPage", component: ChatPage },
    { path: '/test', component: Test },
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
const mountedApp = app.mount("#app")