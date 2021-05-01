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
            notifications: [],
            message_notifications: [],
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
        markChatNotificationsAsRead(state, chat_id){
            let notif = state.message_notifications.filter(e=>e.chat.id == chat_id)
            notif.map(e => state.ws.send(JSON.stringify({
                stream: "message_notifications",
                payload: {
                    action: "mark_as_read",
                    request_id: new Date().getTime(),
                    pk: e.id,
                }
            })))
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
        createWs({ commit, state, dispatch}){
            console.log("Dispatching creating ws")
            commit("createWs")
            state.ws.onopen = function(){
                state.ws.send(JSON.stringify({
                    stream: "message_notifications",
                    payload: {
                        action: "list",
                        request_id: new Date().getTime(),
                    }
                }))
                state.ws.send(JSON.stringify({
                    stream: "chat",
                    payload: {
                        action: "subscribe_to_notifications",
                        request_id: new Date().getTime(),
                    }
                }))
                state.ws.send(JSON.stringify({
                    stream: "message_notifications",
                    payload: {
                        action: "subscribe_to_notifications",
                        request_id: new Date().getTime(),
                    }
                }))
            }
            state.ws.addEventListener("message", function(e){
                let currentChat = router.currentRoute.value.params.id;
                console.log("store event listener", JSON.parse(e.data))
                const data = JSON.parse(e.data)
                switch (data.stream) {
                    case "message_notifications":
                        switch (data.payload.action) {
                            case "mark_as_read":
                                var index = state.message_notifications.findIndex(e => e.id == data.payload.data.id)
                                state.message_notifications[index] = data.payload.data                                
                                break;
                            case "list":
                                state.message_notifications = data.payload.data
                                break;
                            case "create":
                                // TODO don't add if current chat
                                state.message_notifications.push(data.payload.data)
                                if (data.payload.data.chat.id == currentChat
                                    && !data.payload.data.is_read
                                    ){
                                    state.ws.send(JSON.stringify({
                                        stream: "message_notifications",
                                        payload: {
                                            action: "mark_as_read",
                                            request_id: new Date().getTime(),
                                            pk: data.payload.data.id,
                                        }
                                    }))
                                }
                                break;
                            default:
                                break;
                        }
                        break;
                    case "chat":
                        switch (data.payload.action) {
                            case "notification":
                                if (currentChat != data.payload.data.chat.id) 
                                    state.notifications.push(data.payload.data);
                                break;
                        
                            default:
                                break;
                        }
                        break;
                
                    default:
                        break;
                }
            });
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


const NotificationDialog = {
    template: `

    <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 5">
    <div id="liveToast" class="toast hide" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <img src="..." class="rounded me-2" alt="...">
        <strong class="me-auto">Bootstrap</strong>
        <small>11 mins ago</small>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">
        Hello, world! This is a toast message.
      </div>
    </div>
  </div>
    `,
    props: ["notification",],
}


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
        <small class="text-muted p-0 ps-2 m-0">{{parseDate(message.created_at)}}</small>
    </div>
    `,
    props:["message"],
    methods:{
        parseDate(dateString) {
            if(dateString===null) return "-";
            var date = new Date(dateString)
            return date.toLocaleTimeString() + " " + date.toLocaleDateString()
        },
    },
}
const MessageOutgoing = {
    template: `
    <div class="alert alert-info ms-5 p-0">
        <p class="pe-2 pt-1 pb-1 mb-0">{{message.text}}</p>
        <small class="text-muted p-0 pe-2 m-0">{{parseDate(message.created_at)}}</small>
    </div>
    `,
    props:["message"],
    methods:{
        parseDate(dateString) {
            if(dateString===null) return "-";
            var date = new Date(dateString)
            return date.toLocaleTimeString() + " " + date.toLocaleDateString()
        },
    },
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
    },

}

const ContactPage = {
    template: `
    <div>
        <div v-if="status === 'done'" class="container-sm">
            <h3 class="display-6">Contacts page</h3>
            <input type="text" v-model="filterText" class="form-control mt-3 mb-3" placeholder="Search . . ."/>
            <div 
                v-for="user in filteredUsers" :key="user.id" 
                @click="createChat(user)" 
                class="card mb-2"
            >
                <div class="card-body">
                    <p class="m-0 p-0">
                        {{user.username}}
                    </p>
                    <p class="m-0 p-0">
                        <small class="text-muted">
                            Last login: {{parseDate(user.last_login)}}
                        </small>
                    </p>
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
            filterText: "",
        }
    },
    methods: {
        parseDate(dateString) {
            if(dateString===null) return "-";
            var date = new Date(dateString)
            return date.toLocaleTimeString() + " " + date.toLocaleDateString()
        },
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
        filteredUsers(){ return this.filterText.length == 0 ? this.users : this.users.filter(user => user.username.includes(this.filterText));},
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
        <div v-if="notifications.length != 0">
            Notification
        </div>
        <h3 class="display-6">Chats Page</h3>
        <div v-for="chat in chatsOrder" :key="chat.id" @click="openChat(chat)" class="card mb-1">
            <div class="card-body">
                <p class="m-0 p-0">
                    {{otherMember(chat).username}}
                </p>
                <p class="m-0 p-0">
                    <small class="text-muted">
                        {{getLastChatMessage(chat)?.user == currentUser.id ? 'Yo: ': ''}}
                        {{getLastChatMessage(chat)?.text}}
                    </small>
                </p>
            </div>
        </div>
    </div>
    `,
    components: {NotificationDialog, },
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
        chatsOrder(){
            return this.chats.sort(function (a, b){
                if (a.messages[a.messages.length - 1].created_at > b.messages[b.messages.length - 1].created_at)
                    return -1
                if (a.messages[a.messages.length - 1].created_at < b.messages[b.messages.length - 1].created_at)
                    return 1
                return 0
            })
        },
        messageNotifications(){ return this.$store.state.message_notifications;},
        currentUser() { return this.$store.getters.user },
        status() { return this.$store.getters.status; },
        wsConnected() { return this.$store.state.ws.readyState;},
        notifications(){ return this.$store.state.notifications;},
        notifications(){ return this.$store.state.notifications;},
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
            <div v-if="status === 'done'">
                <div v-if="alerts.length > 0" class="alert alert-dismissible fade show">
                    <div v-for="(alert, index) in alerts" :key="index"
                        class="alert alert-info" role="alert"
                    >
                        {{alert.message}}
                        <button @click="removeAlert(alert)" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                </div>
                <ChatPaper :messages="messages" @createMessage="createMessage"/>
            </div>
            <div v-else class="container-sm text-center">
                <div class="spinner-border text-success" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        </div>
    `,
    components: { MessageForm, ChatPaper, NotificationDialog, },
    data() {
        return {
            messages: [],
            members: [],
            chat: [],
            ws: null,
            alerts: [],
        }
    },
    computed: {
        id() { return this.$route.params.id; },
        currentUser() { return this.$store.getters.user; },
        status() { return this.$store.getters.status; },
        notifications(){ return this.$store.state.notifications;},
    },
    methods: {
        removeAlert(alert){
            var index = this.alerts.indexOf(alert)
            if (index > -1) this.alerts.splice(index, 1)
        },
        scrollBottom(){ 
            var el = document.getElementById("scrollBottom")
            if (el) el.scrollIntoView({behavior: 'smooth'});
        },
        createMessage(message) {
            console.log(message)
            const data = {
                stream: "message",
                payload: {
                    action: "create",
                    data:{
                        user: this.currentUser.id,
                        chat: this.id,
                        text: message,
                    },
                    request_id: new Date().getTime(),
                },
            }
            this.$store.state.ws.send(JSON.stringify(data))
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
        onMessageHandler(e){
            const data = JSON.parse(e.data)
            console.log("onMessageHandler", data)
            switch (data.stream) {
                case "message":
                    switch (data.payload.action) {
                        case "create":
                            if (data.payload.data === null) return;
                            this.messages.push(data.payload.data)
                            /**
                             * TODO como agrego esta funciona al resto de funciones como notificaciones?
                             */
                            break;
                        case "notification":
                            if (this.currentUser.id === data.payload.user.id) return;
                            if (!data.payload.message.includes("join")) return;
                            this.alerts.push(data.payload)
                            break;
                        default:
                            break;
                    }
                    break;
            
                default:
                    break;
            }
        }
    },
    created() {
        var self = this;
        this.$store.commit("status", "loading")
        Promise.all([this.getChat(), this.getMessages()])
            .then(([chat_response, message_response]) => {
                console.log("values", chat_response, message_response)
                this.chat = chat_response.data;
                this.messages = message_response.data.results;
                this.members = chat_response.data.members;
                this.$store.state.ws.send(JSON.stringify({
                    stream: "message",
                    payload: {
                        action: "subscribe_to_messages_in_chat",
                        chat: this.id,
                        request_id: new Date().getTime(),
                    },
                }))
                this.$store.state.ws.send(JSON.stringify({
                    stream: "message",
                    payload: {
                        action: "join_chat",
                        chat: this.id,
                        request_id: new Date().getTime(),
                    },
                }))
                this.$store.commit("status", "done")
            })
            .catch(([chat_error, message_error]) => {
                console.log(error)
            })
            this.$store.state.ws.addEventListener("message", this.onMessageHandler);
            // TODO add reconnect
            this.$store.commit("markChatNotificationsAsRead", this.id);
    },
    mounted(){
        this.scrollBottom();
    },
    beforeUnmount(){
        this.$store.state.ws.removeEventListener("message", this.onMessageHandler)
    },
}

const app = createApp({
    el: "#app",
    delimiters: ["[[", "]]"],
    data() {
        return {
            test: "TEST"
        }
    },
    methods: {
        removeNotification(notification){
            var index = this.$store.state.notifications.indexOf(notification)
            if (index > -1) this.$store.state.notifications.splice(index, 1);
        },
        markNotificationAsRead(notification){
            this.ws.send(JSON.stringify({
                stream: "message_notifications",
                payload: {
                    action: "mark_as_read",
                    request_id: new Date().getTime(),
                    pk: notification.id,
                }
            }))
        }
    },
    computed: {
        user() { return this.$store.getters.user; },
        status() { return this.$store.getters.status; },
        notifications(){ return this.$store.state.notifications;},
        ws(){ return this.$store.state.ws;},
        messageNotifications(){ return this.$store.state.message_notifications;},
        currentNotifications(){
            let notifications = this.$store.state.message_notifications;
            if (this.$route.name === "ChatPage")
                return notifications.filter(e => e.chat.id != this.$route.params.id)
            return notifications
        },
        countUnreadNotifications(){ return this.currentNotifications.filter(e => !e.is_read).length;},
    },
    created() {
        this.$store.dispatch("createWs")
    }
})

const routes = [
    { path: '/', name: "ListChatPage", component: ListChatPage },
    { path: '/contacts', name: "ContactPage", component: ContactPage },
    { path: '/chat/:id', name: "ChatPage", component: ChatPage },
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