"""
FaceLock - Interface d'Enrôlement
Version: 1.4 (Avec suppression d'utilisateurs - Droit à l'oubli RGPD)
"""

import customtkinter as ctk
import cv2
import numpy as np
from tkinter import messagebox
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NUM_PHOTOS_FOR_ENROLLMENT = 5
CAPTURE_INTERVAL = 1.0


class EnrollmentGUI:
    def __init__(self, camera, detector, encoder, database):
        self.camera = camera
        self.detector = detector
        self.encoder = encoder
        self.database = database
        
        self.is_capturing = False
        self.captured_embeddings = []
        self.current_photo_count = 0
        self.video_running = False
        
        self.window = ctk.CTk()
        self.window.title("FaceLock - Enrôlement Utilisateur")
        self.window.geometry("700x700")  # Augmenté pour le bouton supprimer
        self.window.resizable(False, False)
        
        if not self.camera.start():
            messagebox.showerror("Erreur", "Impossible d'ouvrir la caméra !")
            self.window.destroy()
            return
        
        self._create_widgets()
        self._start_video()
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.window.mainloop()
    
    def _create_widgets(self):
        title_label = ctk.CTkLabel(
            self.window, 
            text="🔐 FaceLock - Enrôlement", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        self.video_frame = ctk.CTkFrame(self.window, width=400, height=300)
        self.video_frame.pack(pady=5)
        self.video_frame.pack_propagate(False)
        
        import tkinter as tk
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack()
        
        control_frame = ctk.CTkFrame(self.window)
        control_frame.pack(pady=10, padx=20, fill="x")
        
        name_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        name_frame.pack(pady=5, padx=10)
        
        ctk.CTkLabel(name_frame, text="Nom d'utilisateur:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.name_entry = ctk.CTkEntry(name_frame, width=200, placeholder_text="Votre nom")
        self.name_entry.pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(
            control_frame, 
            text="📷 Positionnez votre visage", 
            font=ctk.CTkFont(size=12),
            text_color="yellow"
        )
        self.status_label.pack(pady=5)
        
        counter_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        counter_frame.pack(pady=5)
        
        self.counter_label = ctk.CTkLabel(
            counter_frame, 
            text=f"Photos: 0/{NUM_PHOTOS_FOR_ENROLLMENT}", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.counter_label.pack(side="left", padx=20)
        
        self.progress_bar = ctk.CTkProgressBar(counter_frame, width=200)
        self.progress_bar.pack(side="left", padx=20)
        self.progress_bar.set(0)
        
        # BOUTONS PRINCIPAUX
        button_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        button_frame.pack(pady=15)
        
        self.capture_btn = ctk.CTkButton(
            button_frame,
            text="📸 Démarrer la capture",
            command=self._start_capture,
            width=180,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.capture_btn.pack(side="left", padx=20)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Annuler",
            command=self._on_closing,
            width=120,
            height=35,
            fg_color="#8B0000",
            hover_color="#660000"
        )
        cancel_btn.pack(side="left", padx=20)
        
        # NOUVEAU BOUTON : GESTION DES UTILISATEURS
        manage_btn = ctk.CTkButton(
            self.window,
            text="👥 Gérer les utilisateurs",
            command=self._show_user_management,
            width=250,
            height=35,
            fg_color="#2E8B57",
            hover_color="#3CB371",
            font=ctk.CTkFont(size=14)
        )
        manage_btn.pack(pady=10)
        
        rgpd_label = ctk.CTkLabel(
            self.window,
            text="🔒 RGPD: Embeddings uniquement | Droit à l'oubli disponible",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        rgpd_label.pack(pady=5)
    
    def _show_user_management(self):
        """Affiche l'interface de gestion/suppression des utilisateurs."""
        users = self.database.get_all_users()
        
        if not users:
            messagebox.showinfo("Informations", "Aucun utilisateur enregistré.")
            return
        
        # Créer une fenêtre de gestion
        manage_window = ctk.CTkToplevel(self.window)
        manage_window.title("Gestion des Utilisateurs")
        manage_window.geometry("500x400")
        manage_window.resizable(False, False)
        
        # Titre
        title = ctk.CTkLabel(
            manage_window,
            text="👥 Utilisateurs Enregistrés",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=15)
        
        # Liste des utilisateurs
        list_frame = ctk.CTkFrame(manage_window)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Afficher chaque utilisateur
        user_widgets = []
        for i, user in enumerate(users):
            user_frame = ctk.CTkFrame(list_frame, fg_color="#2b2b2b")
            user_frame.pack(pady=5, padx=10, fill="x")
            
            # Nom de l'utilisateur
            user_label = ctk.CTkLabel(
                user_frame,
                text=f"👤 {user['username']} ({len(user['embedding'])}D)",
                font=ctk.CTkFont(size=14)
            )
            user_label.pack(side="left", padx=10, pady=10)
            
            # Bouton supprimer
            def create_delete_func(username):
                def delete_func():
                    if messagebox.askyesno(
                        "Confirmation",
                        f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{username}' ?\n\n"
                        f"Cette action est irréversible (Droit à l'oubli RGPD)."
                    ):
                        try:
                            self.database.delete_user(username)
                            messagebox.showinfo(
                                "Succès",
                                f"Utilisateur '{username}' supprimé avec succès.\n"
                                f"Toutes ses données biométriques ont été effacées."
                            )
                            manage_window.destroy()
                            self._show_user_management()  # Rafraîchir la liste
                        except Exception as e:
                            messagebox.showerror("Erreur", f"Échec de la suppression:\n{str(e)}")
                return delete_func
            
            delete_btn = ctk.CTkButton(
                user_frame,
                text="🗑️ Supprimer",
                command=create_delete_func(user['username']),
                width=100,
                height=30,
                fg_color="#DC143C",
                hover_color="#8B0000"
            )
            delete_btn.pack(side="right", padx=10, pady=10)
            
            user_widgets.append(user_frame)
        
        # Bouton fermer
        close_btn = ctk.CTkButton(
            manage_window,
            text="❌ Fermer",
            command=manage_window.destroy,
            width=150,
            height=35
        )
        close_btn.pack(pady=15)
    
    def _start_video(self):
        self.video_running = True
        self._update_video_frame()
    
    def _update_video_frame(self):
        if self.video_running:
            frame = self.camera.get_frame()
            
            if frame is not None:
                faces = self.detector.detect_faces(frame)
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                if not faces:
                    cv2.putText(frame, "Aucun visage detecte", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, "Visage detecte !", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display_frame = cv2.resize(rgb_frame, (400, 300))
                
                img = Image.fromarray(display_frame)
                photo = ImageTk.PhotoImage(image=img)
                
                self.video_label.configure(image=photo)
                self.video_label.image = photo
            
            self.window.after(33, self._update_video_frame)
    
    def _start_capture(self):
        username = self.name_entry.get().strip()
        
        if not username:
            messagebox.showwarning("Attention", "Veuillez entrer un nom d'utilisateur !")
            return
        
        if self.is_capturing:
            return
        
        print("🎬 Démarrage de la capture...")
        self.is_capturing = True
        self.captured_embeddings = []
        self.current_photo_count = 0
        self.capture_btn.configure(state="disabled", text="⏳ Capture en cours...")
        self.status_label.configure(text="📸 Capture dans 2 secondes...", text_color="yellow")
        
        self.window.after(2000, self._capture_loop)
    
    def _capture_loop(self):
        """Boucle de capture - VERSION CORRIGÉE."""
        
        if self.current_photo_count >= NUM_PHOTOS_FOR_ENROLLMENT:
            print(f"✅ {NUM_PHOTOS_FOR_ENROLLMENT} photos capturées. Finalisation...")
            self.window.after(500, self._finish_enrollment)
            return
        
        if not self.is_capturing:
            return
        
        frame = self.camera.get_frame()
        
        if frame is not None:
            faces = self.detector.detect_faces(frame)
            
            if faces:
                embedding = self.encoder.get_embedding(frame, faces[0])
                
                if embedding is not None:
                    self.captured_embeddings.append(embedding)
                    self.current_photo_count += 1
                    
                    print(f"📸 Photo {self.current_photo_count}/{NUM_PHOTOS_FOR_ENROLLMENT}")
                    
                    progress = self.current_photo_count / NUM_PHOTOS_FOR_ENROLLMENT
                    self.progress_bar.set(progress)
                    self.counter_label.configure(
                        text=f"Photos: {self.current_photo_count}/{NUM_PHOTOS_FOR_ENROLLMENT}"
                    )
                    self.status_label.configure(
                        text=f"✅ Photo {self.current_photo_count} capturée !", 
                        text_color="green"
                    )
                    
                    if self.current_photo_count >= NUM_PHOTOS_FOR_ENROLLMENT:
                        print("🎯 Dernière photo, finalisation dans 1s...")
                        self.window.after(1000, self._finish_enrollment)
                        return
                else:
                    self.status_label.configure(
                        text="⚠️  Échec encodage", 
                        text_color="orange"
                    )
            else:
                self.status_label.configure(
                    text="⚠️  Aucun visage !", 
                    text_color="orange"
                )
        
        if self.current_photo_count < NUM_PHOTOS_FOR_ENROLLMENT and self.is_capturing:
            self.window.after(int(CAPTURE_INTERVAL * 1000), self._capture_loop)
    
    def _finish_enrollment(self):
        """Finalisation - VERSION CORRIGÉE."""
        print("🔄 Finalisation en cours...")
        
        self.is_capturing = False
        self.capture_btn.configure(state="normal", text="📸 Démarrer la capture")
        
        print(f"📊 Embeddings capturés: {len(self.captured_embeddings)}")
        
        if len(self.captured_embeddings) < 3:
            messagebox.showerror(
                "Échec", 
                f"Seulement {len(self.captured_embeddings)} photos valides.\n"
                f"Minimum requis: 3"
            )
            self._reset_capture()
            return
        
        embeddings_array = np.array(self.captured_embeddings)
        average_embedding = np.mean(embeddings_array, axis=0)
        
        norm = np.linalg.norm(average_embedding)
        if norm > 0:
            average_embedding = average_embedding / norm
        
        username = self.name_entry.get().strip()
        
        try:
            print(f"💾 Enregistrement de l'utilisateur: {username}")
            success = self.database.add_user(username, average_embedding)
            
            if success:
                print("✅ Utilisateur enregistré avec succès !")
                messagebox.showinfo(
                    "Succès ! 🎉",
                    f"Utilisateur '{username}' enregistré !\n\n"
                    f"📊 Détails:\n"
                    f"- Photos: {len(self.captured_embeddings)}\n"
                    f"- Embedding: {average_embedding.shape[0]}D\n"
                    f"- Photos: EFFACÉES (RGPD)"
                )
                self._on_closing()
            else:
                messagebox.showerror(
                    "Erreur",
                    f"L'utilisateur '{username}' existe déjà !"
                )
                self._reset_capture()
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            messagebox.showerror("Erreur", f"Échec:\n{str(e)}")
            self._reset_capture()
    
    def _reset_capture(self):
        self.is_capturing = False
        self.captured_embeddings = []
        self.current_photo_count = 0
        self.capture_btn.configure(state="normal", text="📸 Démarrer la capture")
        self.progress_bar.set(0)
        self.counter_label.configure(text=f"Photos: 0/{NUM_PHOTOS_FOR_ENROLLMENT}")
        self.status_label.configure(
            text="📷 Positionnez votre visage", 
            text_color="yellow"
        )
    
    def _on_closing(self):
        self.is_capturing = False
        self.video_running = False
        self.camera.stop()
        self.window.destroy()


if __name__ == "__main__":
    print("⚠️  Utilisez 'python main.py --enroll'")