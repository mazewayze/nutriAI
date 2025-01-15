import streamlit as st
import openai
import re
from pathlib import Path
import requests
from PIL import Image
import io
import base64

# Configuration de la page Streamlit
st.set_page_config(page_title="Assistant Nutritionniste IA", page_icon="🥗", layout="wide")

# Initialisation des variables de session Streamlit
if 'all_meals' not in st.session_state:
    st.session_state.all_meals = []
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = {}

# Configuration OpenAI
openai.api_key = 'openAIAPIKEY'

def extract_meals(text):
    """Extrait tous les repas entre crochets d'un texte donné."""
    pattern = r'\[(.*?)\]'
    return re.findall(pattern, text)

def generate_and_save_image(prompt, save_folder="generated_meal_images"):
    """Génère une image pour un repas donné et retourne l'image encodée en base64."""
    try:
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        
        response = openai.Image.create(
            prompt=f"A professional food photography of {prompt}, high quality, appetizing",
            n=1,
            size="1024x1024"
        )
        
        image_url = response['data'][0]['url']
        
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        return None
    
    except Exception as e:
        st.error(f"Erreur lors de la génération de l'image: {str(e)}")
        return None

# Interface Streamlit
st.title("🥗 Assistant Nutritionniste IA")
st.write("Je suis votre expert en nutrition personnel. Posez-moi vos questions sur l'alimentation!")

# Sidebar pour les paramètres et l'historique des repas
with st.sidebar:
    st.header("Repas Suggérés")
    for meal, image_data in st.session_state.generated_images.items():
        if st.button(meal):
            st.image(f"data:image/png;base64,{image_data}", caption=meal)
            st.write("Détails du repas :")
            # Vous devrez implémenter une logique pour stocker et récupérer ces informations
            st.write("Calories : X")
            st.write("Protéines : X g")
            st.write("Glucides : X g")
            st.write("Lipides : X g")

# Zone de chat principale
user_input = st.chat_input("Posez votre question ici...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Réflexion en cours..."):
            try:
                # Initialisation pour le streaming
                response_container = st.empty()
                assistant_response = ""
                
                # Appel avec streaming activé
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """Vous êtes un expert en nutrition professionnel spécialisé dans la création de plans alimentaires. 
                        Mettez tous les noms de repas entre crochets comme cela: [Salade César au poulet grillé].
                        Pour chaque repas suggéré, fournissez également une recette détaillée, les ingrédients nécessaires, et les informations nutritionnelles (calories, protéines, glucides, lipides)."""},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    stream=True  # Activation du streaming
                )
                
                # Traitement des chunks de réponse
                for chunk in response:
                    chunk_text = chunk['choices'][0]['delta'].get('content', '')
                    assistant_response += chunk_text
                    response_container.markdown(assistant_response)
                
                # Extraction et traitement des nouveaux repas
                new_meals = extract_meals(assistant_response)
                if new_meals:
                    st.success(f"Nouveaux repas détectés: {len(new_meals)}")
                    
                    cols = st.columns(min(len(new_meals), 3))
                    for i, meal in enumerate(new_meals):
                        with cols[i % 3]:
                            st.write(f"{meal}")
                            with st.spinner(f"Génération de l'image pour {meal}..."):
                                image = generate_and_save_image(meal)
                                if image:
                                    st.session_state.generated_images[meal] = image
                                    st.image(f"data:image/png;base64,{image}", caption=meal)
                    
                    st.session_state.all_meals.extend(new_meals)
                
            except Exception as e:
                st.error(f"Erreur: {str(e)}")


# Bouton pour réinitialiser la conversation
if st.button("Réinitialiser la conversation"):
    st.session_state.all_meals = []
    st.session_state.conversation = []
    st.session_state.generated_images = {}
    st.success("Conversation réinitialisée!")