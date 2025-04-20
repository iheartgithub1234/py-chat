import socket
import threading
from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.ttk import Separator

class ChatClient:
    def __init__(self):
        # First create the root window but don't display it yet
        self.root = Tk()
        self.root.withdraw()  # Hide the main window temporarily
        
        # Get client name using the dialog
        self.client_name = ""
        while not self.client_name:
            self.client_name = simpledialog.askstring("Name", "Enter your name:", parent=self.root)
            if not self.client_name:
                if not messagebox.askretrycancel("Name Required", "You must enter a name to join the chat."):
                    self.root.destroy()
                    exit()
        
        # Now setup the main window
        self.root.deiconify()  # Show the main window
        self.root.title(f"Chat Client - {self.client_name}")
        self.root.geometry("500x600")
        self.root.configure(bg="#121212")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.client_socket = None
        self.connected = False
        
        # Make the window resizable
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = Frame(self.root, bg="#1e1e1e", padx=10, pady=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = Label(header_frame, text=f"Chat as {self.client_name}", font=("Arial", 12, "bold"), 
                               fg="#4fc3f7", bg="#1e1e1e")
        self.title_label.pack(side=LEFT)
        
        self.status_label = Label(header_frame, text="Status: Disconnected", font=("Arial", 10), 
                                fg="#bbbbbb", bg="#1e1e1e")
        self.status_label.pack(side=RIGHT)
        
        # Separator
        Separator(self.root, orient='horizontal').grid(row=1, column=0, sticky="ew")
        
        # Chat display
        self.chat_display = Text(self.root, wrap=WORD, state=DISABLED, bg="#1e1e1e", 
                               fg="#ffffff", insertbackground="white", padx=10, pady=10)
        self.chat_display.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # Scrollbar
        scrollbar = Scrollbar(self.root, command=self.chat_display.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        # Message entry
        message_frame = Frame(self.root, bg="#121212", padx=10, pady=10)
        message_frame.grid(row=3, column=0, sticky="ew")
        
        self.message_entry = Entry(message_frame, bg="#2d2d2d", fg="white", 
                                 insertbackground="white", relief=FLAT)
        self.message_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = Button(message_frame, text="Send", command=self.send_message,
                                bg="#0d47a1", fg="white", activebackground="#1565c0",
                                activeforeground="white", relief=FLAT)
        self.send_button.pack(side=RIGHT, padx=5)
        
        # Connect button
        self.connect_button = Button(self.root, text="Connect to Server", command=self.connect_to_server,
                                   bg="#0d47a1", fg="white", activebackground="#1565c0",
                                   activeforeground="white", relief=FLAT)
        self.connect_button.grid(row=4, column=0, pady=10, sticky="ew", padx=10)
        
        # Configure tag colors
        self.chat_display.tag_config("system", foreground="#4fc3f7")
        self.chat_display.tag_config("join", foreground="#81c784")
        self.chat_display.tag_config("leave", foreground="#ff8a65")
        self.chat_display.tag_config("error", foreground="#ff5252")
        self.chat_display.tag_config("you", foreground="#4fc3f7")
        
        # Connect to server automatically
        self.connect_to_server()
    
    def display_message(self, message, tag=None):
        self.chat_display.config(state=NORMAL)
        self.chat_display.insert(END, message + "\n", tag)
        self.chat_display.config(state=DISABLED)
        self.chat_display.see(END)
    
    def connect_to_server(self):
        if self.connected:
            return
            
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', 5555))
            
            # Send client name to server
            self.client_socket.send(self.client_name.encode('utf-8'))
            
            self.connected = True
            self.status_label.config(text="Status: Connected")
            self.connect_button.config(state=DISABLED)
            self.display_message("Connected to server", "system")
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {str(e)}")
            self.status_label.config(text="Status: Disconnected")
    
    def disconnect_from_server(self):
        if self.connected:
            try:
                self.client_socket.send("CLIENT_DISCONNECT".encode('utf-8'))
                self.client_socket.close()
            except:
                pass
            
            self.connected = False
            self.status_label.config(text="Status: Disconnected")
            self.connect_button.config(state=NORMAL)
            self.display_message("Disconnected from server", "system")
    
    def send_message(self, event=None):
        if not self.connected:
            messagebox.showerror("Not Connected", "You are not connected to the server.")
            return
            
        message = self.message_entry.get().strip()
        if message:
            try:
                formatted_message = f"{self.client_name}:{message}"
                self.client_socket.send(formatted_message.encode('utf-8'))
                self.display_message(f"You: {message}", "you")
                self.message_entry.delete(0, END)
            except Exception as e:
                messagebox.showerror("Send Error", f"Failed to send message: {str(e)}")
                self.disconnect_from_server()
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                
                if not message:
                    self.disconnect_from_server()
                    break
                
                if message == "SERVER_SHUTDOWN":
                    self.display_message("Server has been shut down", "system")
                    self.disconnect_from_server()
                    break
                
                # Check for system messages
                if message.startswith("SYSTEM:"):
                    self.display_message(message[7:], "system")
                else:
                    # Regular message format: "sender:message"
                    if ":" in message:
                        sender, msg = message.split(":", 1)
                        self.display_message(f"{sender}: {msg}")
            except:
                self.disconnect_from_server()
                break
    
    def on_closing(self):
        if self.connected:
            self.disconnect_from_server()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()