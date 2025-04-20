import socket
import threading
from tkinter import *
from tkinter import scrolledtext, messagebox
from tkinter.ttk import Separator

class ChatServer:
    def __init__(self):
        self.server_socket = None
        self.clients = {}
        self.running = False
        
        # Create server GUI
        self.root = Tk()
        self.root.title("Chat Server")
        self.root.geometry("600x500")
        self.root.configure(bg="#121212")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Make the window resizable
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = Frame(self.root, bg="#1e1e1e", padx=10, pady=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = Label(header_frame, text="Chat Server", font=("Arial", 16, "bold"), 
                              fg="#4fc3f7", bg="#1e1e1e")
        self.title_label.pack(side=LEFT)
        
        self.status_label = Label(header_frame, text="Status: Offline", font=("Arial", 10), 
                                 fg="#bbbbbb", bg="#1e1e1e")
        self.status_label.pack(side=RIGHT)
        
        # Separator
        Separator(self.root, orient='horizontal').grid(row=1, column=0, sticky="ew")
        
        # Chat log
        self.chat_log = scrolledtext.ScrolledText(self.root, wrap=WORD, state=DISABLED, 
                                                bg="#1e1e1e", fg="#ffffff", insertbackground="white",
                                                padx=10, pady=10)
        self.chat_log.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # Control buttons
        button_frame = Frame(self.root, bg="#121212", padx=10, pady=10)
        button_frame.grid(row=3, column=0, sticky="ew")
        
        self.start_button = Button(button_frame, text="Start Server", command=self.start_server,
                                  bg="#0d47a1", fg="white", activebackground="#1565c0",
                                  activeforeground="white", relief=FLAT)
        self.start_button.pack(side=LEFT, padx=5)
        
        self.stop_button = Button(button_frame, text="Stop Server", command=self.stop_server,
                                 bg="#b71c1c", fg="white", activebackground="#c62828",
                                 activeforeground="white", relief=FLAT, state=DISABLED)
        self.stop_button.pack(side=LEFT, padx=5)
        
        # Configure tag colors
        self.chat_log.tag_config("system", foreground="#4fc3f7")
        self.chat_log.tag_config("join", foreground="#81c784")
        self.chat_log.tag_config("leave", foreground="#ff8a65")
        self.chat_log.tag_config("error", foreground="#ff5252")
        
    def log_message(self, message, tag=None):
        self.chat_log.config(state=NORMAL)
        self.chat_log.insert(END, message + "\n", tag)
        self.chat_log.config(state=DISABLED)
        self.chat_log.see(END)
    
    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('0.0.0.0', 5555))
            self.server_socket.listen(5)
            
            self.running = True
            self.status_label.config(text="Status: Online (Port: 5555)")
            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            
            self.log_message("Server started on port 5555", "system")
            self.log_message("Waiting for connections...", "system")
            
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
        except Exception as e:
            messagebox.showerror("Server Error", f"Failed to start server: {str(e)}")
    
    def stop_server(self):
        if self.server_socket:
            self.running = False
            
            # Close all client connections
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.send("SERVER_SHUTDOWN".encode('utf-8'))
                    client_socket.close()
                except:
                    pass
            
            # Close server socket
            try:
                self.server_socket.close()
            except:
                pass
            
            self.clients.clear()
            self.status_label.config(text="Status: Offline")
            self.start_button.config(state=NORMAL)
            self.stop_button.config(state=DISABLED)
            self.log_message("Server has been stopped", "system")
    
    def accept_connections(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                
                # Get client name
                client_name = client_socket.recv(1024).decode('utf-8')
                
                self.clients[client_socket] = client_name
                
                self.log_message(f"{client_name} has joined the chat from {client_address[0]}", "join")
                
                # Broadcast join message to all clients
                self.broadcast_message(f"SYSTEM:{client_name} has joined the chat", client_socket)
                
                # Start a thread for the client
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except:
                if self.running:
                    self.log_message("Error accepting connection", "error")
                break
    
    def handle_client(self, client_socket):
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                
                if not message:
                    break
                    
                if message == "CLIENT_DISCONNECT":
                    break
                
                # Format: "CLIENT_NAME:message"
                if ":" in message:
                    sender, msg = message.split(":", 1)
                    formatted_msg = f"{sender}: {msg}"
                    self.log_message(formatted_msg)
                    self.broadcast_message(message, client_socket)
            except:
                break
        
        # Client disconnected
        if client_socket in self.clients:
            client_name = self.clients[client_socket]
            del self.clients[client_socket]
            client_socket.close()
            
            self.log_message(f"{client_name} has left the chat", "leave")
            self.broadcast_message(f"SYSTEM:{client_name} has left the chat", client_socket)
    
    def broadcast_message(self, message, sender_socket=None):
        for client_socket in self.clients:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    # Remove broken connections
                    if client_socket in self.clients:
                        client_name = self.clients[client_socket]
                        del self.clients[client_socket]
                        self.log_message(f"Lost connection with {client_name}", "error")
    
    def on_closing(self):
        if self.running:
            if messagebox.askokcancel("Quit", "Server is running. Do you want to stop it and quit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    server = ChatServer()
    server.run()