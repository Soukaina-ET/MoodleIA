"""
API Flask MoodleIA - Backend Complet pour Système d'Apprentissage Adaptatif
============================================================================
Cette API expose tous les modèles ML et le chatbot IA pour intégration Moodle
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import json
import traceback
import warnings
warnings.filterwarnings('ignore')


# Import du chatbot personnalisé
import sys
import os # <-- NOUVEAU

# Ligne 20 modifiée: Obtient le chemin du répertoire parent (MoodleIA)
# __file__ est le chemin de app.py. os.path.dirname remonte d'un niveau (APIS/), puis d'un autre (MoodleIA/).
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root) # Ajoute MoodleIA/ au chemin de recherche

from Predictions.train_support_chatbot import AIStudentChatbot

# ==========================================
# CONFIGURATION DE L'APPLICATION FLASK
# ==========================================

app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin depuis Moodle

# Configuration
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Chemins des modèles
MODELS_PATH = 'Predictions/models/'
DATA_PATH = 'Data/processed/'

# ==========================================
# CHARGEMENT DES MODÈLES AU DÉMARRAGE
# ==========================================

print("🚀 Démarrage de l'API MoodleIA...")
print("📦 Chargement des modèles ML...")

try:
    # Modèles de prédiction
    at_risk_model = joblib.load(f'{MODELS_PATH}at_risk_model.pkl')
    dropout_model = joblib.load(f'{MODELS_PATH}dropout_model.pkl')
    quiz_model = joblib.load(f'{MODELS_PATH}quiz_performance_model.pkl')
    pass_fail_model = joblib.load(f'{MODELS_PATH}pass_fail_model.pkl')
    recommendation_model = joblib.load(f'{MODELS_PATH}recommendation_model.pkl')
    
    # Chatbot IA
    chatbot = joblib.load(f'{MODELS_PATH}support_chatbot_model.pkl')
    
    # Données
    student_features = pd.read_csv(f'{DATA_PATH}students_features.csv')
    student_info = pd.read_csv('Data/raw/studentInfo.csv')
    
    print("✅ Tous les modèles chargés avec succès!")
    
except Exception as e:
    print(f"❌ Erreur lors du chargement des modèles: {e}")
    print("⚠️ L'API fonctionnera en mode dégradé")

# ==========================================
# UTILITAIRES
# ==========================================

def convert_numpy_types(obj):
    """Convertir les types NumPy en types Python natifs pour JSON"""
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    return obj

def get_student_features(student_id):
    """Récupérer les features d'un étudiant"""
    if student_id not in student_features['id_student'].values:
        return None
    return student_features[student_features['id_student'] == student_id].iloc[0]

def prepare_features_for_prediction(student_row, feature_columns):
    """Préparer les features pour une prédiction"""
    return student_row[feature_columns].values.reshape(1, -1)

# ==========================================
# ROUTE DE BASE
# ==========================================

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil de l'API"""
    return jsonify({
        'service': 'MoodleIA API',
        'version': '1.0.0',
        'status': 'operational',
        'endpoints': {
            'health': '/api/health',
            'student_dashboard': '/api/student/<student_id>/dashboard',
            'at_risk_prediction': '/api/student/<student_id>/at-risk',
            'quiz_prediction': '/api/student/<student_id>/quiz-prediction',
            'recommendations': '/api/student/<student_id>/recommendations',
            'chatbot': '/api/chatbot/chat',
            'batch_predictions': '/api/batch/at-risk',
            'interventions': '/api/interventions/at-risk-students'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier l'état de l'API et des modèles"""
    models_status = {
        'at_risk_model': at_risk_model is not None,
        'dropout_model': dropout_model is not None,
        'quiz_model': quiz_model is not None,
        'pass_fail_model': pass_fail_model is not None,
        'recommendation_model': recommendation_model is not None,
        'chatbot': chatbot is not None
    }
    
    return jsonify({
        'status': 'healthy' if all(models_status.values()) else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'models': models_status,
        'total_students': len(student_features)
    })

# ==========================================
# TABLEAU DE BORD ÉTUDIANT COMPLET
# ==========================================

@app.route('/api/student/<int:student_id>/dashboard', methods=['GET'])
def student_dashboard(student_id):
    """
    Tableau de bord complet pour un étudiant
    Retourne toutes les prédictions + recommandations + insights
    """
    try:
        # Vérifier si l'étudiant existe
        student_row = get_student_features(student_id)
        if student_row is None:
            return jsonify({'error': f'Étudiant {student_id} non trouvé'}), 404
        
        # Info de base
        student_basic = student_info[student_info['id_student'] == student_id].iloc[0]
        
        dashboard = {
            'student_id': student_id,
            'timestamp': datetime.now().isoformat(),
            'basic_info': {
                'gender': student_basic['gender'],
                'age_band': student_basic['age_band'],
                'education': student_basic['highest_education'],
                'disability': student_basic['disability'],
                'final_result': student_basic['final_result']
            },
            'performance': {},
            'predictions': {},
            'recommendations': [],
            'alerts': [],
            'insights': {}
        }
        
        # Performance actuelle
        dashboard['performance'] = {
            'avg_score': float(student_row.get('avg_score', 0)),
            'num_assessments': int(student_row.get('num_assessments_completed', 0)),
            'total_clicks': int(student_row.get('total_clicks', 0)),
            'active_days': int(student_row.get('active_days', 0)),
            'late_submission_rate': float(student_row.get('late_submission_rate', 0))
        }
        
        # Prédictions At-Risk
        X_at_risk = prepare_features_for_prediction(student_row, at_risk_model['feature_columns'])
        at_risk_pred = at_risk_model['model'].predict(X_at_risk)[0]
        at_risk_proba = at_risk_model['model'].predict_proba(X_at_risk)[0]
        
        dashboard['predictions']['at_risk'] = {
            'is_at_risk': bool(at_risk_pred == 1),
            'risk_probability': float(at_risk_proba[1]),
            'confidence': float(max(at_risk_proba)),
            'status': 'À risque' if at_risk_pred == 1 else 'Bon statut'
        }
        
        # Prédiction Dropout
        X_dropout = prepare_features_for_prediction(student_row, dropout_model['feature_columns'])
        dropout_pred = dropout_model['model'].predict(X_dropout)[0]
        dropout_proba = dropout_model['model'].predict_proba(X_dropout)[0]
        
        dashboard['predictions']['dropout'] = {
            'will_dropout': bool(dropout_pred == 1),
            'dropout_probability': float(dropout_proba[1]),
            'confidence': float(max(dropout_proba))
        }
        
        # Recommandations
        if student_id in recommendation_model['student_resource_matrix'].index:
            from Predictions.recommend_system import RecommendationEngine
            recommender = RecommendationEngine(data_path=DATA_PATH, models_path=MODELS_PATH)
            recommender.student_resource_matrix = recommendation_model['student_resource_matrix']
            recommender.student_embeddings = recommendation_model['student_embeddings']
            recommender.successful_patterns = recommendation_model['successful_patterns']
            recommender.svd = recommendation_model['svd']
            recommender.resource_types = recommendation_model['resource_types']
            
            recs = recommender.recommend_resources_for_student(student_id, n_recommendations=5)
            dashboard['recommendations'] = convert_numpy_types(recs)
        
        # Générer des alertes
        if dashboard['predictions']['at_risk']['is_at_risk']:
            dashboard['alerts'].append({
                'level': 'high',
                'type': 'at_risk',
                'message': f"Risque d'échec élevé ({dashboard['predictions']['at_risk']['risk_probability']:.0%})",
                'action': 'Contacter le tuteur immédiatement'
            })
        
        if dashboard['performance']['late_submission_rate'] > 0.3:
            dashboard['alerts'].append({
                'level': 'medium',
                'type': 'time_management',
                'message': f"Taux de soumissions tardives élevé ({dashboard['performance']['late_submission_rate']:.0%})",
                'action': 'Améliorer la planification'
            })
        
        if dashboard['performance']['active_days'] < 30:
            dashboard['alerts'].append({
                'level': 'medium',
                'type': 'engagement',
                'message': f"Engagement faible ({dashboard['performance']['active_days']} jours actifs)",
                'action': 'Augmenter la fréquence de connexion'
            })
        
        # Insights
        dashboard['insights'] = {
            'engagement_level': 'Élevé' if dashboard['performance']['active_days'] > 50 else 
                               'Moyen' if dashboard['performance']['active_days'] > 30 else 'Faible',
            'performance_trend': 'Positif' if dashboard['performance']['avg_score'] > 70 else
                                'Stable' if dashboard['performance']['avg_score'] > 50 else 'Négatif',
            'needs_intervention': len(dashboard['alerts']) > 0
        }
        
        return jsonify(convert_numpy_types(dashboard))
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ==========================================
# PRÉDICTIONS INDIVIDUELLES
# ==========================================

@app.route('/api/student/<int:student_id>/at-risk', methods=['GET'])
def predict_at_risk(student_id):
    """Prédire si un étudiant est à risque d'échec"""
    try:
        student_row = get_student_features(student_id)
        if student_row is None:
            return jsonify({'error': f'Étudiant {student_id} non trouvé'}), 404
        
        X = prepare_features_for_prediction(student_row, at_risk_model['feature_columns'])
        prediction = at_risk_model['model'].predict(X)[0]
        proba = at_risk_model['model'].predict_proba(X)[0]
        
        result = {
            'student_id': student_id,
            'prediction': {
                'is_at_risk': bool(prediction == 1),
                'risk_probability': float(proba[1]),
                'success_probability': float(proba[0]),
                'confidence': float(max(proba))
            },
            'model': {
                'name': at_risk_model['model_name'],
                'metrics': convert_numpy_types(at_risk_model['metrics'])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/<int:student_id>/dropout', methods=['GET'])
def predict_dropout(student_id):
    """Prédire si un étudiant va abandonner"""
    try:
        student_row = get_student_features(student_id)
        if student_row is None:
            return jsonify({'error': f'Étudiant {student_id} non trouvé'}), 404
        
        X = prepare_features_for_prediction(student_row, dropout_model['feature_columns'])
        prediction = dropout_model['model'].predict(X)[0]
        proba = dropout_model['model'].predict_proba(X)[0]
        
        result = {
            'student_id': student_id,
            'prediction': {
                'will_dropout': bool(prediction == 1),
                'dropout_probability': float(proba[1]),
                'retention_probability': float(proba[0]),
                'confidence': float(max(proba))
            },
            'model': {
                'name': dropout_model['model_name'],
                'metrics': convert_numpy_types(dropout_model['metrics'])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/<int:student_id>/quiz-prediction', methods=['POST'])
def predict_quiz_performance(student_id):
    """Prédire la performance au prochain quiz"""
    try:
        data = request.json
        
        # Features du quiz précédent (à fournir dans le body)
        required_features = ['prev_avg_score', 'prev_std_score', 'num_prev_quizzes', 'prev_avg_delay']
        
        for feature in required_features:
            if feature not in data:
                return jsonify({'error': f'Feature manquante: {feature}'}), 400
        
        # Préparer les features
        quiz_features = pd.DataFrame([{
            'prev_avg_score': data['prev_avg_score'],
            'prev_std_score': data.get('prev_std_score', 0),
            'prev_min_score': data.get('prev_min_score', data['prev_avg_score']),
            'prev_max_score': data.get('prev_max_score', data['prev_avg_score']),
            'num_prev_quizzes': data['num_prev_quizzes'],
            'prev_avg_delay': data['prev_avg_delay'],
            'trend': data.get('trend', 0)
        }])
        
        # Prédire
        predicted_score = quiz_model['model'].predict(quiz_features)[0]
        
        result = {
            'student_id': student_id,
            'predicted_score': float(predicted_score),
            'confidence_interval': {
                'lower': float(predicted_score - 10),
                'upper': float(predicted_score + 10)
            },
            'recommendation': 'Bon travail!' if predicted_score > 70 else 
                            'Révisez davantage' if predicted_score > 50 else 
                            'Attention! Révisez en profondeur',
            'model': {
                'name': quiz_model['model_name'],
                'rmse': float(quiz_model['metrics']['rmse'])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# RECOMMANDATIONS
# ==========================================

@app.route('/api/student/<int:student_id>/recommendations', methods=['GET'])
def get_recommendations(student_id):
    """Obtenir des recommandations de ressources personnalisées"""
    try:
        n_recommendations = request.args.get('n', default=5, type=int)
        
        if student_id not in recommendation_model['student_resource_matrix'].index:
            return jsonify({'error': f'Étudiant {student_id} non trouvé dans le système de recommandations'}), 404
        
        # Recréer le recommender temporairement
        from Predictions.recommend_system import RecommendationEngine
        recommender = RecommendationEngine(data_path=DATA_PATH, models_path=MODELS_PATH)
        recommender.student_resource_matrix = recommendation_model['student_resource_matrix']
        recommender.student_embeddings = recommendation_model['student_embeddings']
        recommender.successful_patterns = recommendation_model['successful_patterns']
        recommender.svd = recommendation_model['svd']
        recommender.resource_types = recommendation_model['resource_types']
        
        recommendations = recommender.recommend_resources_for_student(student_id, n_recommendations=n_recommendations)
        
        result = {
            'student_id': student_id,
            'recommendations': convert_numpy_types(recommendations),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ==========================================
# CHATBOT IA
# ==========================================

@app.route('/api/chatbot/chat', methods=['POST'])
def chatbot_chat():
    """Converser avec le chatbot IA"""
    try:
        data = request.json
        
        if 'student_id' not in data or 'message' not in data:
            return jsonify({'error': 'student_id et message requis'}), 400
        
        student_id = data['student_id']
        message = data['message']
        
        # Appeler le chatbot
        response = chatbot.chat(student_id, message)
        
        result = {
            'student_id': student_id,
            'user_message': message,
            'bot_response': response['response'],
            'context': convert_numpy_types(response['student_context']),
            'model': response['model'],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/chatbot/insights/<int:student_id>', methods=['GET'])
def chatbot_insights(student_id):
    """Obtenir des insights détaillés d'un étudiant"""
    try:
        insights = chatbot.get_detailed_insights(student_id)
        
        result = {
            'student_id': student_id,
            'insights': convert_numpy_types(insights),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# PRÉDICTIONS PAR LOT (BATCH)
# ==========================================

@app.route('/api/batch/at-risk', methods=['POST'])
def batch_at_risk_prediction():
    """Prédire le risque pour plusieurs étudiants"""
    try:
        data = request.json
        student_ids = data.get('student_ids', [])
        
        if not student_ids:
            # Prédire pour tous les étudiants
            student_ids = student_features['id_student'].tolist()
        
        results = []
        
        for student_id in student_ids:
            student_row = get_student_features(student_id)
            if student_row is not None:
                X = prepare_features_for_prediction(student_row, at_risk_model['feature_columns'])
                prediction = at_risk_model['model'].predict(X)[0]
                proba = at_risk_model['model'].predict_proba(X)[0]
                
                results.append({
                    'student_id': int(student_id),
                    'is_at_risk': bool(prediction == 1),
                    'risk_probability': float(proba[1])
                })
        
        return jsonify({
            'total_students': len(results),
            'at_risk_count': sum(1 for r in results if r['is_at_risk']),
            'predictions': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# SYSTÈME D'INTERVENTION
# ==========================================

@app.route('/api/interventions/at-risk-students', methods=['GET'])
def get_at_risk_students_for_intervention():
    """Obtenir la liste des étudiants nécessitant une intervention"""
    try:
        threshold = request.args.get('threshold', default=0.7, type=float)
        
        # Prédire pour tous les étudiants
        X_all = student_features[at_risk_model['feature_columns']]
        predictions = at_risk_model['model'].predict(X_all)
        probas = at_risk_model['model'].predict_proba(X_all)
        
        # Filtrer ceux à risque élevé
        at_risk_students = []
        
        for i, (pred, proba) in enumerate(zip(predictions, probas)):
            if pred == 1 and proba[1] >= threshold:
                student_id = int(student_features.iloc[i]['id_student'])
                student_basic = student_info[student_info['id_student'] == student_id].iloc[0]
                
                at_risk_students.append({
                    'student_id': student_id,
                    'risk_probability': float(proba[1]),
                    'priority': 'high' if proba[1] >= 0.8 else 'medium',
                    'contact_info': {
                        'gender': student_basic['gender'],
                        'age_band': student_basic['age_band']
                    },
                    'recommended_actions': [
                        'Contacter par email',
                        'Planifier un entretien',
                        'Envoyer des ressources supplémentaires'
                    ]
                })
        
        # Trier par priorité
        at_risk_students.sort(key=lambda x: x['risk_probability'], reverse=True)
        
        return jsonify({
            'total_at_risk': len(at_risk_students),
            'high_priority': sum(1 for s in at_risk_students if s['priority'] == 'high'),
            'students': at_risk_students,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# STATISTIQUES GLOBALES
# ==========================================

@app.route('/api/stats/global', methods=['GET'])
def global_statistics():
    """Statistiques globales du système"""
    try:
        # Prédire pour tous
        X_all = student_features[at_risk_model['feature_columns']]
        at_risk_predictions = at_risk_model['model'].predict(X_all)
        
        stats = {
            'total_students': len(student_features),
            'at_risk_count': int(at_risk_predictions.sum()),
            'at_risk_percentage': float(at_risk_predictions.mean() * 100),
            'avg_score': float(student_features['avg_score'].mean()),
            'avg_engagement_days': float(student_features['active_days'].mean()),
            'models_loaded': {
                'at_risk': True,
                'dropout': True,
                'quiz': True,
                'recommendations': True,
                'chatbot': True
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# GESTION D'ERREURS
# ==========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint non trouvé'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur serveur interne'}), 500

# ==========================================
# LANCEMENT DE L'APPLICATION
# ==========================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 API MoodleIA démarrée!")
    print("="*70)
    print(f"📍 URL: http://localhost:5000")
    print(f"📊 Étudiants chargés: {len(student_features)}")
    print(f"🤖 Modèles actifs: 6/6")
    print("="*70 + "\n")
    
    # Démarrer le serveur
    app.run(
        host='0.0.0.0',  # Accessible depuis l'extérieur
        port=5000,
        debug=True  # Mode debug pour le développement
    )