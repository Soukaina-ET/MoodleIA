"""
Chatbot de Support Intelligent avec API Hugging Face (Sérialisable)
================================================================
Utilise l'API Hugging Face Inference Router (OpenAI compatible client)
Ajout des méthodes __getstate__ et __setstate__ pour permettre l'enregistrement
et le chargement via joblib/pickle, en excluant les objets OpenAI non sérialisables.
"""

import pandas as pd
import numpy as np
import joblib
import json
import requests
from datetime import datetime
import warnings
from openai import OpenAI
from typing import Any, Dict, List
import time
warnings.filterwarnings('ignore')

# ==========================================
# FONCTION UTILITAIRE POUR LA SÉRIALISATION JSON (CORRIGÉE NUMPY 2.0)
# ==========================================
def _convert_to_json_serializable(obj: Any) -> Any:
    """
    Convertit les types NumPy non sérialisables (int64, float64, etc.) en types Python natifs.
    Corrigé pour la version NumPy 2.0 en remplaçant les anciens alias.
    """
    if isinstance(obj, (np.int64, np.intc, np.intp, np.int8,
                        np.int16, np.int32, np.uint8,
                        np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float16, np.float32)): 
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_json_serializable(v) for v in obj]
    else:
        return obj


class AIStudentChatbot:
    """
    Chatbot intelligent utilisant l'API Hugging Face Inference Router (via client OpenAI)
    """
    
    def __init__(self, 
                 data_path: str = 'Data/processed/', 
                 models_path: str = 'Predictions/models/',
                 hf_token: str | None = "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", 
                 model_name: str = 'mistralai/Mistral-7B-Instruct-v0.2',
                 skip_client_init: bool = False): # Ajout d'un flag pour le chargement
        
        self.data_path = data_path
        self.models_path = models_path
        self.hf_token = hf_token
        self.model_name = model_name
        self.conversation_history: List[Dict[str, Any]] = []

        # Initialisation du client OpenAI seulement si nécessaire
        self.client = None
        self.hf_router_model = f"{model_name}:featherless-ai" 
        
        if not skip_client_init:
            self.init_openai_client()
        
        # Charger les données et modèles prédictifs
        self.load_prediction_models()
        
        print(f"✅ Chatbot initialisé avec {model_name}")
        print(f"  Mode: API Hugging Face Router (via client OpenAI)")
        if hf_token:
            print(f"  Token: Configuré ✓ (Limite plus élevée)")
        else:
            print(f"  Token: Non configuré (Utilisation en mode limité)")

    # NOUVELLE MÉTHODE : Initialisation du client API
    def init_openai_client(self):
        """Initialise le client OpenAI pour l'API Hugging Face Router."""
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=self.hf_token if self.hf_token else "DUMMY_TOKEN",
        )

    # MÉTHODE MAGIQUE : Ce qui est sauvegardé lors du joblib.dump
    def __getstate__(self):
        """Retourne l'état de l'objet, en excluant les objets non sérialisables."""
        state = self.__dict__.copy()
        # Exclure le client OpenAI non sérialisable
        if 'client' in state:
            del state['client']
        return state

    # MÉTHODE MAGIQUE : Ce qui est fait lors du joblib.load
    def __setstate__(self, state):
        """Restaure l'état de l'objet et réinitialise le client OpenAI."""
        self.__dict__.update(state)
        # Recréer le client OpenAI
        self.init_openai_client()

    # Le reste des méthodes...
    # ... (load_prediction_models, get_student_context, create_prompt, etc.)

    def load_prediction_models(self):
        """Charger tous les modèles prédictifs et données"""
        print("\n📥 Chargement des modèles et données...")
        
        try:
            # Modèles ML
            self.at_risk_model = joblib.load(f'{self.models_path}at_risk_model.pkl')
            self.quiz_model = joblib.load(f'{self.models_path}quiz_performance_model.pkl')
            self.recommendation_model = joblib.load(f'{self.models_path}recommendation_model.pkl')
            
            # Données
            self.student_features = pd.read_csv(f'{self.data_path}students_features.csv')
            self.student_info = pd.read_csv('Data/raw/studentInfo.csv')
            self.student_assessment = pd.read_csv('Data/raw/studentAssessment.csv')
            self.assessments = pd.read_csv('Data/raw/assessments.csv')
            self.student_vle = pd.read_csv('Data/raw/studentVle.csv')
            
            print("✅ Modèles et données chargés")
            
        except Exception as e:
            print(f"⚠️ Erreur: {e}")
    
    def get_student_context(self, student_id: int) -> Dict[str, Any]:
        """Récupérer et formater le contexte de l'étudiant"""
        context: Dict[str, Any] = {}
        
        if student_id in self.student_info['id_student'].values:
            info = self.student_info[self.student_info['id_student'] == student_id].iloc[0]
            context['demographics'] = {
                'gender': info['gender'],
                'age_band': info['age_band'],
                'education': info['highest_education'],
                'final_result': info['final_result']
            }
        
        if student_id in self.student_features['id_student'].values:
            features = self.student_features[self.student_features['id_student'] == student_id].iloc[0]
            context['performance'] = {
                'avg_score': float(features.get('avg_score', 0)),
                'num_assessments': int(features.get('num_assessments_completed', 0)),
                'total_clicks': int(features.get('total_clicks', 0)),
                'active_days': int(features.get('active_days', 0)),
                'late_submission_rate': float(features.get('late_submission_rate', 0))
            }
        
        try:
            features_row = self.student_features[self.student_features['id_student'] == student_id]
            X = features_row[self.at_risk_model['feature_columns']]
            prediction = self.at_risk_model['model'].predict(X)[0]
            proba = self.at_risk_model['model'].predict_proba(X)[0]
            
            context['risk_analysis'] = {
                'is_at_risk': bool(prediction == 1),
                'risk_probability': float(proba[1]),
                'status': 'À risque' if prediction == 1 else 'Bon statut'
            }
        except:
            context['risk_analysis'] = {'status': 'Non disponible'}
        
        vle_recent = self.student_vle[self.student_vle['id_student'] == student_id]
        if len(vle_recent) > 0:
            context['engagement'] = {
                'total_interactions': int(vle_recent['sum_click'].sum()),
                'recent_activity': 'Actif' if vle_recent['sum_click'].sum() > 100 else 'Faible'
            }
        
        return context
    
    def create_prompt(self, student_context: Dict[str, Any], user_message: str) -> str:
        """Créer le prompt complet pour le LLM (Format Mistral-Instruct)"""
        
        perf = student_context.get('performance', {})
        risk = student_context.get('risk_analysis', {})
        demo = student_context.get('demographics', {})
        
        prompt = f"""<s>[INST] Tu es un assistant pédagogique intelligent et empathique pour étudiants en ligne.

CONTEXTE DE L'ÉTUDIANT:
- Niveau d'études: {demo.get('education', 'N/A')}
- Score moyen: {perf.get('avg_score', 0):.1f}/100
- Nombre d'évaluations: {perf.get('num_assessments', 0)}
- Jours actifs: {perf.get('active_days', 0)}
- Statut académique: {risk.get('status', 'N/A')}
- Probabilité de réussite: {(1 - risk.get('risk_probability', 0)):.0%}
- Taux de soumissions tardives: {perf.get('late_submission_rate', 0):.0%}

TON RÔLE:
1. Réponds de manière empathique et personnalisée
2. Fournis des conseils concrets basés sur les données réelles
3. Encourage et motive l'étudiant
4. Identifie les problèmes et propose des solutions actionnables
5. Utilise un ton amical, professionnel et encourageant
6. Sois bref et direct (maximum 150 mots)

QUESTION DE L'ÉTUDIANT:
{user_message}

RÉPONSE (en français, courte et personnalisée): [/INST]"""
        
        return prompt
    
    def call_huggingface_api(self, prompt: str, max_tokens: int = 250, temperature: float = 0.7) -> str:
        """
        Appeler l'API Hugging Face Inference Router via le client OpenAI
        """
        if self.client is None:
            return "⚠️ Erreur: Le client API n'est pas initialisé. Redémarrez la session ou vérifiez le chargement."
            
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.hf_router_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            generated_text = completion.choices[0].message.content
            
            if generated_text:
                generated_text = generated_text.strip()
                return generated_text
            else:
                raise ValueError("Réponse vide de l'API LLM.")
        
        except Exception as e:
            error_message = str(e)
            
            if "Timeout" in error_message or "read timed out" in error_message:
                return "⏱️ Le serveur met trop de temps à répondre. Veuillez réessayer."
            elif "429" in error_message or "rate limit" in error_message:
                return "⚠️ Limite de requêtes atteinte. Veuillez attendre quelques instants (ou utilisez un token)."
            else:
                print(f"Erreur lors de l'appel API (Router): {error_message}")
                return self.generate_fallback_response(prompt)
    
    def generate_fallback_response(self, user_message: str) -> str:
        """Réponse de secours basée sur les règles (identique à votre implémentation)"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['score', 'note', 'résultat', 'performance']):
            return """📊 Je peux analyser vos performances! Selon vos données:

• Consultez votre tableau de bord pour voir vos scores détaillés
• Comparez vos résultats avec les objectifs du cours
• Identifiez les points à améliorer

💡 Astuce: Concentrez-vous sur la compréhension plutôt que la mémorisation."""
        
        elif any(word in message_lower for word in ['risque', 'échec', 'échouer', 'danger']):
            return """⚠️ Je comprends votre préoccupation. Voici ce que je vous recommande:

1. 📞 Contactez votre tuteur cette semaine
2. 📚 Revoyez les concepts de base
3. 👥 Rejoignez un groupe d'étude
4. ⏰ Créez un planning d'étude régulier

🌟 Rappelez-vous: chaque difficulté est une opportunité d'apprentissage!"""
        
        elif any(word in message_lower for word in ['aide', 'conseil', 'recommandation', 'améliorer']):
            return """💡 Conseils personnalisés pour vous:

1. Consultez les ressources quotidiennement (15-20 min minimum)
2. Faites les exercices pratiques
3. Posez des questions sur le forum
4. Planifiez vos révisions avant chaque évaluation

📚 N'hésitez pas à demander de l'aide à votre tuteur - c'est leur rôle!"""
        
        elif any(word in message_lower for word in ['motivation', 'découragé', 'abandonner', 'difficile']):
            return """💪 Je comprends que ce soit difficile parfois. Voici ce qui peut vous aider:

• Célébrez chaque petite victoire
• Prenez des pauses régulières
• Connectez-vous avec d'autres étudiants
• Rappelez-vous pourquoi vous avez commencé

🌟 Vous avez déjà fait beaucoup de progrès. Continuez!"""
        
        elif any(word in message_lower for word in ['engagement', 'activité', 'connexion', 'temps']):
            return """📈 Pour améliorer votre engagement:

• Fixez un horaire d'étude régulier
• Consultez les ressources au moins 4 fois par semaine
• Participez aux discussions du forum
• Complétez les activités interactives

⏰ Même 30 minutes par jour font une grande différence!"""
        
        else:
            return """👋 Bonjour! Je suis votre assistant pédagogique personnel.

Je peux vous aider avec:
• 📊 Vos résultats et performances
• ⚠️ Évaluation de votre risque d'échec
• 💡 Conseils personnalisés d'étude
• 📈 Amélioration de votre engagement
• 💪 Motivation et soutien

Comment puis-je vous aider aujourd'hui?"""
    
    def chat(self, student_id: int, user_message: str) -> Dict[str, Any]:
        """Interface principale pour interagir avec le chatbot"""
        
        print(f"\n💬 Question: {user_message}")
        print("🤖 Génération de la réponse...")
        
        student_context = self.get_student_context(student_id)
        prompt = self.create_prompt(student_context, user_message)
        response = self.call_huggingface_api(prompt)
        
        if not response or len(response) < 20 or "Erreur" in response or "Timeout" in response or "Limite" in response:
            response = self.generate_fallback_response(user_message)
        
        # Sauvegarder dans l'historique
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'student_id': student_id,
            'user_message': user_message,
            'bot_response': response,
            'context': _convert_to_json_serializable(student_context), 
            'model': self.model_name
        })
        
        return {
            'response': response,
            'student_context': student_context,
            'model': self.model_name
        }
    
    def get_detailed_insights(self, student_id: int) -> Dict[str, Any]:
        """Obtenir des insights détaillés sur un étudiant"""
        context = self.get_student_context(student_id)
        
        insights = {
            'student_id': student_id,
            'risk_level': context.get('risk_analysis', {}).get('status', 'Unknown'),
            'performance_summary': context.get('performance', {}),
            'engagement_level': context.get('engagement', {}).get('recent_activity', 'Unknown'),
            'recommendations': []
        }
        
        perf = context.get('performance', {})
        risk = context.get('risk_analysis', {})
        
        risk_proba = risk.get('risk_probability', 0) # Utiliser risk.get('risk_probability')
        if risk.get('is_at_risk', False) and risk_proba > 0.5:
            insights['recommendations'].append({
                'priority': 'high',
                'action': 'Rencontrer le tuteur immédiatement',
                'reason': f"Risque d'échec de {risk_proba:.0%}"
            })
        
        late_rate = perf.get('late_submission_rate', 0)
        if late_rate > 0.3:
            insights['recommendations'].append({
                'priority': 'medium',
                'action': 'Améliorer la gestion du temps',
                'reason': f"Taux de soumissions tardives: {late_rate:.0%}"
            })
        
        active_days = perf.get('active_days', 0)
        if active_days < 30:
            insights['recommendations'].append({
                'priority': 'medium',
                'action': 'Augmenter la fréquence de connexion',
                'reason': f"Seulement {active_days} jours actifs"
            })
        
        avg_score = perf.get('avg_score', 0)
        if avg_score < 50:
            insights['recommendations'].append({
                'priority': 'high',
                'action': 'Revoir les concepts fondamentaux',
                'reason': f"Score moyen faible: {avg_score:.1f}/100"
            })
        
        return insights
    
    def save_conversation_history(self):
        """Sauvegarder l'historique des conversations"""
        filename = f'{self.models_path}chatbot_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        history_json_safe = _convert_to_json_serializable(self.conversation_history)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history_json_safe, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Historique sauvegardé: {filename}")
        return filename

    # NOUVELLE MÉTHODE : Sauvegarde du modèle
    def save_model(self, filename: str = 'support_chatbot_model.pkl'):
        """Sauvegarde l'instance complète du chatbot (hors client API) avec joblib."""
        filepath = f'{self.models_path}{filename}'
        try:
            joblib.dump(self, filepath)
            print(f"\n📦 Modèle du Chatbot sauvegardé sous: {filepath}")
        except Exception as e:
            print(f"\n❌ Échec de la sauvegarde du modèle avec joblib: {e}")


# ==========================================
# SCRIPT D'EXÉCUTION ET TESTS
# ==========================================

if __name__ == "__main__":
    print("="*70)
    print("🤖 CHATBOT IA - API HUGGING FACE (Sérialisation Ajoutée)")
    print("="*70)
    
    # Configuration
    CHATBOT_MODEL_FILENAME = 'support_chatbot_model.pkl'
    
    # Initialiser le chatbot
    chatbot = AIStudentChatbot(
        data_path='Data/processed/',
        models_path='Predictions/models/',
        hf_token="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",
        model_name='mistralai/Mistral-7B-Instruct-v0.2'
    )
    
    # Tester avec un étudiant
    print("\n" + "="*70)
    print("🧪 TESTS DU CHATBOT")
    print("="*70)
    
    try:
        test_student_id = chatbot.student_info['id_student'].iloc[0]
        print(f"Étudiant testé: ID {test_student_id}")
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture des données étudiantes : {e}")
        test_student_id = 123456
        
    
    test_questions = [
        "Bonjour, comment vont mes études?",
        "Est-ce que je risque d'échouer?",
    ]
    
    for question in test_questions:
        print(f"\n{'='*70}")
        print(f"👤 Étudiant: {question}")
        print('-'*70)
        
        response = chatbot.chat(test_student_id, question)
        print(f"🤖 Assistant:\n{response['response']}")
        print(f"\n📊 Contexte: Risque = {response['student_context'].get('risk_analysis', {}).get('status', 'N/A')}")
        
        time.sleep(2)
    
    # ==========================================
    # ENREGISTREMENT FINAL DU MODÈLE (selon votre demande)
    # ==========================================
    print("\n" + "="*70)
    print("📦 ENREGISTREMENT DU MODÈLE")
    print("="*70)
    chatbot.save_model(filename=CHATBOT_MODEL_FILENAME)
    
    # ==========================================
    # TEST DE CHARGEMENT POUR VÉRIFICATION
    # ==========================================
    print("\n" + "="*70)
    print("🔄 TEST DE CHARGEMENT (Simulé)")
    print("="*70)
    
    try:
        # Charger l'instance sauvegardée
        loaded_chatbot = joblib.load(f'{chatbot.models_path}{CHATBOT_MODEL_FILENAME}')
        
        print(f"✅ Chargement réussi de l'instance: {loaded_chatbot.model_name}")
        
        # Test rapide après chargement (vérifie la réinitialisation du client API)
        response_test_load = loaded_chatbot.chat(test_student_id, "Bonjour après rechargement, ça fonctionne ?")
        print(f"🤖 Assistant (rechargé):\n{response_test_load['response']}")
        
    except Exception as e:
        print(f"❌ Échec du test de chargement: {e}")
    
    print("\n" + "="*70)
    print("✅ CHATBOT OPÉRATIONNEL!")
    print("="*70)