const { createApp } = Vue
const { createRouter, createWebHistory } = VueRouter
const { createStore } = Vuex

const ws_schema = window.location.protocol === "http:" ? "ws:" : "wss:";
const host = window.location.host;

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
            status: "done"
        }
    },
    getters: {
        user: (state) => state.currentUser,
        status: (state) => state.status,
        isAuth: (state) => state.currentUser ? true : false,
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
        }
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
    <div class="type_msg">
        <form @submit.prevent="submitForm" class="input_msg_write">
            <input v-model="message" type="text" class="write_msg" placeholder="Type a message" />
            <button class="msg_send_btn" type="button"><i class="fa fa-paper-plane-o" aria-hidden="true"></i></button>
        </form>
    </div>
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
    template: `
    <div class="incoming_msg">
        <div class="incoming_msg_img"> <img src="https://ptetutorials.com/images/user-profile.png" alt="sunil">
        </div>
        <div class="received_msg">
            <div class="received_withd_msg">
                <p>{{message.text}}</p>
                <span class="time_date">{{message.created_at}}</span>
            </div>
        </div>
    </div>
    `,
    props:["message"],
}
const MessageOutgoing = {
    template: `
    <div class="outgoing_msg">
        <div class="sent_msg">
            <p>{{message.text}}</p>
            <span class="time_date">{{message.created_at}}</span>
        </div>
    </div>
    `,
    props:["message"],
}


const ChatPaper = {
    template: `
    <div class="mesgs">
        <div class="msg_history">
            <span v-for="message in messages">
            <MessageOutgoing v-if="message.user.id == currentUser.id" :message="message" />
            <MessageIncoming v-else :message="message" />
            </span>
            <span id="scrollBottom"></span>
        </div>
        <MessageForm @submitForm="createMessage"/>
    </div>
    `,
    components: {MessageIncoming, MessageOutgoing, MessageForm,},
    props:["messages"],
    emits:["createMessage"],
    computed:{
        currentUser(){return this.$store.getters.user;},
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
    mounted(){
        this.scrollBottom();
    }

}

const Test = {
    template: `
        <div class="mesgs">
            <div class="msg_history">
                <div class="incoming_msg">
                    <div class="incoming_msg_img"> <img src="https://ptetutorials.com/images/user-profile.png"
                            alt="sunil">
                    </div>
                    <div class="received_msg">
                        <div class="received_withd_msg">
                            <p>Test which is a new approach to have all
                                solutions</p>
                            <span class="time_date"> 11:01 AM | June 9</span>
                        </div>
                    </div>
                </div>
                <div class="outgoing_msg">
                    <div class="sent_msg">
                        <p>Test which is a new approach to have all
                            solutions</p>
                        <span class="time_date"> 11:01 AM | June 9</span>
                    </div>
                </div>
                <div class="incoming_msg">
                    <div class="incoming_msg_img"> <img src="https://ptetutorials.com/images/user-profile.png"
                            alt="sunil">
                    </div>
                    <div class="received_msg">
                        <div class="received_withd_msg">
                            <p>Test, which is a new approach to have</p>
                            <span class="time_date"> 11:01 AM | Yesterday</span>
                        </div>
                    </div>
                </div>
                <div class="outgoing_msg">
                    <div class="sent_msg">
                        <p>Apollo University, Delhi, India Test</p>
                        <span class="time_date"> 11:01 AM | Today</span>
                    </div>
                </div>
                <div class="incoming_msg">
                    <div class="incoming_msg_img"> <img src="https://ptetutorials.com/images/user-profile.png"
                            alt="sunil">
                    </div>
                    <div class="received_msg">
                        <div class="received_withd_msg">
                            <p>We work directly with our designers and suppliers,
                                and sell direct to you, which means quality, exclusive
                                products, at a price anyone can afford.</p>
                            <span class="time_date"> 11:01 AM | Today</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="type_msg">
                <div class="input_msg_write">
                    <input type="text" class="write_msg" placeholder="Type a message" />
                    <button class="msg_send_btn" type="button"><i class="fa fa-paper-plane-o"
                            aria-hidden="true"></i></button>
                </div>
            </div>
        </div>
    `,
}

const ContactPage = {
    template: `
    <div>
        <h3>Contacts page</h3>
        <div v-for="user in users" :key="user.id" style="border: 1px solid black">
        {{user.username}}
        <button @click="createChat(user)">Chat with him</button>
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
    <div>
        <div v-if="status === 'done'">
            <h3>Chats Page</h3>
            <div v-for="chat in chats" :key="chat.id" style="border: 1px solid black">
                {{chat.id}}
                <button @click="openChat(chat)">Ingresar</button>
            </div>
        </div>
        <div v-else>Loading</div>
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
    },
    computed: {
        currentUser() { return this.$store.getters.user },
        status() { return this.$store.getters.status; },
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
            <div v-if="ws.readyState === ws.CLOSED" class="alert">
                WEB SOCKET NO CONECTADO 
            </div>
                <ChatPaper :messages="messages" @createMessage="createMessage"/>
          
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
        this.createWebsocket();
    },
    mounted(){
        // this.scrollBottom();
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