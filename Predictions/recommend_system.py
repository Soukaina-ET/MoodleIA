"""
Système de Recommandations pour OULAD
======================================
Recommande des ressources pédagogiques personnalisées basées sur:
- Le profil de l'étudiant
- Son historique d'apprentissage
- Les patterns des étudiants similaires qui ont réussi
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import warnings
warnings.filterwarnings('ignore')


class RecommendationEngine:
    """
    Moteur de recommandations hybride combinant:
    - Collaborative Filtering (similarité entre étudiants)
    - Content-Based Filtering (caractéristiques des ressources)
    - Performance-Based (ressources utilisées par étudiants performants)
    """
    
    def __init__(self, data_path='Data/processed/', models_path='Predictions/models/'):
        self.data_path = data_path
        self.models_path = models_path
        self.scaler = StandardScaler()
        
    def load_data(self):
        """Charger toutes les données nécessaires"""
        print("📥 Chargement des données pour recommandations...")
        
        # Données principales
        self.student_features = pd.read_csv(f'{self.data_path}students_features.csv')
        self.recommendations_data = pd.read_csv(f'{self.data_path}recommendations_data.csv')
        
        # Données brutes pour enrichissement
        self.student_vle = pd.read_csv('Data/raw/studentVle.csv')
        self.vle = pd.read_csv('Data/raw/vle.csv')
        self.student_info = pd.read_csv('Data/raw/studentInfo.csv')
        
        print(f"✅ Données chargées:")
        print(f"   - Étudiants: {len(self.student_features)}")
        print(f"   - Interactions VLE: {len(self.student_vle)}")
        
    def create_student_resource_matrix(self):
        """Créer une matrice étudiant-ressource pour collaborative filtering"""
        print("\n📊 Création de la matrice étudiant-ressource...")
        
        # Merger pour avoir les types de ressources
        vle_detailed = self.student_vle.merge(
            self.vle[['id_site', 'activity_type']], 
            on='id_site'
        )
        
        # Agréger par étudiant et type de ressource
        student_resource = vle_detailed.groupby(
            ['id_student', 'activity_type']
        )['sum_click'].sum().reset_index()
        
        # Créer une matrice pivot
        matrix = student_resource.pivot_table(
            index='id_student',
            columns='activity_type',
            values='sum_click',
            fill_value=0
        )
        
        # Normaliser (pour que les étudiants très actifs ne dominent pas)
        matrix_normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
        
        self.student_resource_matrix = matrix_normalized
        self.resource_types = list(matrix.columns)
        
        print(f"✅ Matrice créée: {matrix.shape[0]} étudiants × {matrix.shape[1]} types de ressources")
        
        return matrix_normalized
    
    def build_collaborative_model(self):
        """Construire un modèle de collaborative filtering"""
        print("\n🤝 Construction du modèle collaborative filtering...")
        
        # Réduction de dimensionnalité avec SVD
        n_components = min(50, len(self.resource_types) - 1)
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        
        # Transformer la matrice
        self.student_embeddings = self.svd.fit_transform(self.student_resource_matrix)
        
        print(f"✅ SVD appliqué: {n_components} composantes")
        print(f"   Variance expliquée: {self.svd.explained_variance_ratio_.sum():.2%}")
        
    def find_similar_students(self, student_id, n_similar=10):
        """Trouver les étudiants similaires basés sur leurs patterns d'utilisation"""
        
        # Vérifier si l'étudiant existe dans la matrice
        if student_id not in self.student_resource_matrix.index:
            return []
        
        # Obtenir l'index de l'étudiant
        student_idx = self.student_resource_matrix.index.get_loc(student_id)
        
        # Calculer la similarité cosinus
        student_embedding = self.student_embeddings[student_idx].reshape(1, -1)
        similarities = cosine_similarity(student_embedding, self.student_embeddings)[0]
        
        # Obtenir les indices des étudiants les plus similaires (exclure l'étudiant lui-même)
        similar_indices = similarities.argsort()[::-1][1:n_similar+1]
        
        # Obtenir les IDs et scores de similarité
        similar_students = [
            {
                'id_student': self.student_resource_matrix.index[idx],
                'similarity_score': similarities[idx]
            }
            for idx in similar_indices
        ]
        
        return similar_students
    
    def get_successful_student_patterns(self):
        """Identifier les patterns de ressources utilisées par les étudiants qui réussissent"""
        print("\n🎯 Analyse des patterns des étudiants performants...")
        
        # Merger avec les résultats
        student_results = self.student_info[['id_student', 'final_result']]
        
        # Identifier les étudiants performants (Pass ou Distinction)
        successful_students = student_results[
            student_results['final_result'].isin(['Pass', 'Distinction'])
        ]['id_student'].unique()
        
        # Filtrer la matrice pour ces étudiants
        successful_matrix = self.student_resource_matrix[
            self.student_resource_matrix.index.isin(successful_students)
        ]
        
        # Calculer la moyenne d'utilisation par type de ressource
        self.successful_patterns = successful_matrix.mean(axis=0).sort_values(ascending=False)
        
        print(f"✅ Patterns analysés pour {len(successful_students)} étudiants performants")
        print("\n📚 Top 5 ressources utilisées par les étudiants qui réussissent:")
        for resource, score in self.successful_patterns.head().items():
            print(f"   - {resource}: {score:.3f}")
        
        return self.successful_patterns
    
    def recommend_resources_for_student(self, student_id, n_recommendations=5):
        """
        Générer des recommandations personnalisées pour un étudiant
        """
        recommendations = []
        
        # Vérifier si l'étudiant existe
        if student_id not in self.student_resource_matrix.index:
            print(f"⚠️ Étudiant {student_id} non trouvé dans les données")
            return self._get_popular_recommendations(n_recommendations)
        
        # 1. Collaborative Filtering: ressources aimées par étudiants similaires
        similar_students = self.find_similar_students(student_id, n_similar=10)
        
        if similar_students:
            similar_ids = [s['id_student'] for s in similar_students]
            similar_matrix = self.student_resource_matrix.loc[similar_ids]
            collaborative_scores = similar_matrix.mean(axis=0)
        else:
            collaborative_scores = pd.Series(0, index=self.resource_types)
        
        # 2. Content-Based: ressources que l'étudiant n'a pas beaucoup utilisées
        student_usage = self.student_resource_matrix.loc[student_id]
        unexplored_resources = 1 - student_usage  # Plus c'est proche de 1, moins c'est exploré
        
        # 3. Performance-Based: ressources utilisées par étudiants performants
        performance_scores = self.successful_patterns
        
        # Combiner les scores (pondération)
        combined_scores = (
            0.4 * collaborative_scores +
            0.3 * unexplored_resources +
            0.3 * performance_scores
        )
        
        # Trier et obtenir les top recommandations
        top_resources = combined_scores.sort_values(ascending=False).head(n_recommendations)
        
        # Formater les recommandations
        for resource_type, score in top_resources.items():
            recommendations.append({
                'resource_type': resource_type,
                'recommendation_score': float(score),
                'reason': self._generate_reason(
                    resource_type, 
                    student_usage[resource_type],
                    collaborative_scores[resource_type],
                    performance_scores[resource_type]
                )
            })
        
        return recommendations
    
    def _generate_reason(self, resource_type, student_usage, collab_score, perf_score):
        """Générer une explication pour la recommandation"""
        reasons = []
        
        if student_usage < 0.1:
            reasons.append("Vous n'avez pas encore exploré cette ressource")
        
        if collab_score > 0.3:
            reasons.append("Fortement utilisée par des étudiants similaires à vous")
        
        if perf_score > 0.3:
            reasons.append("Corrélée avec la réussite dans ce cours")
        
        return " • ".join(reasons) if reasons else "Ressource recommandée pour compléter votre apprentissage"
    
    def _get_popular_recommendations(self, n_recommendations=5):
        """Recommandations par défaut basées sur la popularité"""
        popular = self.student_resource_matrix.mean(axis=0).sort_values(ascending=False).head(n_recommendations)
        
        recommendations = []
        for resource_type, score in popular.items():
            recommendations.append({
                'resource_type': resource_type,
                'recommendation_score': float(score),
                'reason': "Ressource populaire auprès des étudiants"
            })
        
        return recommendations
    
    def recommend_for_at_risk_students(self):
        """Générer des recommandations spécifiques pour les étudiants à risque"""
        print("\n⚠️ Génération de recommandations pour étudiants à risque...")
        
        # Charger le modèle at-risk
        try:
            at_risk_model = joblib.load(f'{self.models_path}at_risk_model.pkl')
            at_risk_predictions = at_risk_model['model'].predict(
                self.student_features[at_risk_model['feature_columns']]
            )
            at_risk_students = self.student_features[at_risk_predictions == 1]['id_student'].values
        except:
            print("⚠️ Modèle at-risk non trouvé, utilisation des résultats finaux")
            at_risk_students = self.student_info[
                self.student_info['final_result'].isin(['Fail', 'Withdrawn'])
            ]['id_student'].values
        
        # Pour chaque étudiant à risque, identifier les ressources qui pourraient les aider
        at_risk_recommendations = []
        
        for student_id in at_risk_students[:100]:  # Limiter pour l'exemple
            if student_id in self.student_resource_matrix.index:
                recs = self.recommend_resources_for_student(student_id, n_recommendations=3)
                
                at_risk_recommendations.append({
                    'id_student': student_id,
                    'recommendations': recs
                })
        
        print(f"✅ Recommandations générées pour {len(at_risk_recommendations)} étudiants à risque")
        
        return at_risk_recommendations
    
    def generate_resource_insights(self):
        """Générer des insights sur l'utilisation des ressources"""
        print("\n📈 Génération des insights sur les ressources...")
        
        insights = {
            'most_used_overall': self.student_resource_matrix.sum(axis=0).sort_values(ascending=False).head(5).to_dict(),
            'most_correlated_with_success': self.successful_patterns.head(5).to_dict(),
            'least_used': self.student_resource_matrix.sum(axis=0).sort_values().head(5).to_dict(),
            'resource_diversity_by_performance': {}
        }
        
        # Analyser la diversité des ressources par niveau de performance
        for result in ['Pass', 'Distinction', 'Fail', 'Withdrawn']:
            students = self.student_info[self.student_info['final_result'] == result]['id_student'].unique()
            students_in_matrix = [s for s in students if s in self.student_resource_matrix.index]
            
            if students_in_matrix:
                diversity = (self.student_resource_matrix.loc[students_in_matrix] > 0).sum(axis=1).mean()
                insights['resource_diversity_by_performance'][result] = float(diversity)
        
        print("✅ Insights générés")
        return insights
    
    def save_recommendation_model(self):
        """Sauvegarder le modèle de recommandations"""
        print("\n💾 Sauvegarde du modèle de recommandations...")
        
        model_info = {
            'svd': self.svd,
            'student_embeddings': self.student_embeddings,
            'student_resource_matrix': self.student_resource_matrix,
            'resource_types': self.resource_types,
            'successful_patterns': self.successful_patterns,
            'scaler': self.scaler
        }
        
        joblib.dump(model_info, f'{self.models_path}recommendation_model.pkl')
        print(f"✅ Modèle sauvegardé: {self.models_path}recommendation_model.pkl")

    def run_full_pipeline(self):
        """Exécuter le pipeline complet de recommandations"""
        print("="*70)
        print("🎯 DÉMARRAGE DU SYSTÈME DE RECOMMANDATIONS")
        print("="*70)
        
        # 1. Charger les données
        self.load_data()
        
        # 2. Créer la matrice étudiant-ressource
        self.create_student_resource_matrix()
        
        # 3. Construire le modèle collaborative
        self.build_collaborative_model()
        
        # 4. Identifier les patterns de succès
        self.get_successful_student_patterns()
        
        # 5. Générer des insights
        insights = self.generate_resource_insights()
        
        # 6. Tester sur quelques étudiants
        print("\n🧪 Test de recommandations sur 3 étudiants:")
        sample_students = self.student_resource_matrix.index[:3]
        
        for student_id in sample_students:
            print(f"\n📚 Recommandations pour étudiant {student_id}:")
            recs = self.recommend_resources_for_student(student_id, n_recommendations=3)
            for i, rec in enumerate(recs, 1):
                print(f"   {i}. {rec['resource_type']} (score: {rec['recommendation_score']:.3f})")
                print(f"      → {rec['reason']}")
        
        # 7. Recommandations pour étudiants à risque
        at_risk_recs = self.recommend_for_at_risk_students()
        
        # 8. Sauvegarder le modèle
        self.save_recommendation_model()
        
        print("\n" + "="*70)
        print("✅ SYSTÈME DE RECOMMANDATIONS PRÊT!")
        print("="*70)
        
        return insights, at_risk_recs



def calculate_metrics_temporal_split(recommender_instance, student_id, k=3):
    """
    Calcule les métriques en utilisant une séparation temporelle (ex: Semaine 5 comme coupure).
    Les recommandations sont basées sur l'historique < Semaine 5, 
    et la vérité terrain est l'utilisation > Semaine 5.
    """
    
    # Étape 1: Identifier les interactions de test (après la Semaine 5, par exemple)
    # Dans OULAD, la 'date' est le nombre de jours depuis le début du cours.
    CUTOFF_DATE = 35 # 5 semaines * 7 jours
    
    # ⚠️ NOTE : Cette opération nécessite d'accéder à student_vle (disponible dans recommender_instance)
    student_test_interactions = recommender_instance.student_vle[
        (recommender_instance.student_vle['id_student'] == student_id) & 
        (recommender_instance.student_vle['date'] > CUTOFF_DATE)
    ]

    # Étape 2: Déterminer les 'Relevant Resources'
    # Les ressources pertinentes sont celles effectivement utilisées par l'étudiant après la coupure
    if student_test_interactions.empty:
        # L'étudiant n'a plus interagi, pas de vérité terrain pour l'évaluation.
        return 0.0, 0.0

    # Merger avec les types d'activité
    vle_test_detailed = student_test_interactions.merge(
        recommender_instance.vle[['id_site', 'activity_type']], 
        on='id_site'
    )
    
    # Les ressources pertinentes sont les types d'activité cliqués APRÈS la coupure.
    relevant_resources = set(vle_test_detailed['activity_type'].unique())
    
    # --- Modèle de recommandation ---
    # Pour que ce test soit parfait, le modèle devrait idéalement être entraîné 
    # SANS les données > CUTOFF_DATE. 
    # Ici, nous réutilisons le modèle entraîné sur toutes les données.
    recommendations = recommender_instance.recommend_resources_for_student(student_id, n_recommendations=k)
    recommended_resources = set([rec['resource_type'] for rec in recommendations])

    # --- Calcul des métriques ---
    hits = len(relevant_resources.intersection(recommended_resources))
    
    # Rappel : Parmi les ressources pertinentes, combien le modèle a-t-il capturé ?
    recall_at_k = hits / len(relevant_resources)
    
    # Précision : Parmi les K recommandations, combien étaient pertinentes ?
    precision_at_k = hits / k
    
    return recall_at_k, precision_at_k
# ==========================================
# SCRIPT D'EXÉCUTION
# ==========================================

if __name__ == "__main__":
    # Initialiser le système
    recommender = RecommendationEngine(
        data_path='Data/processed/',
        models_path='Predictions/models/'
    )
    
    # Exécuter le pipeline complet
    insights, at_risk_recommendations = recommender.run_full_pipeline()
    
    print("\n🎉 Système de recommandations opérationnel!")
    print("💡 Utilisez recommender.recommend_resources_for_student(student_id) pour obtenir des recommandations")
    # ... après l'exécution de recommender.run_full_pipeline() ...

    '''print("\n📊 ÉVALUATION Recommend System (Recall@3 et Precision@3)")
    recall_scores = []
    precision_scores = []
    sample_students = recommender.student_resource_matrix.index[100:200] 

    for student_id in sample_students:
        recall, precision = calculate_metrics_at_k(recommender, student_id, k=3)
        recall_scores.append(recall)
        precision_scores.append(precision)

    avg_recall = np.mean(recall_scores)
    avg_precision = np.mean(precision_scores)
    
    print(f"✅ Recall@3 moyen pour l'échantillon: {avg_recall:.4f}")
    print(f"✅ Precision@3 moyen pour l'échantillon: {avg_precision:.4f}")'''
    # Dans le SCRIPT D'EXÉCUTION (__main__) :
# ...
    print("\n📊 ÉVALUATION Recommend System (Séparation Temporelle K=3)")
    recall_scores = []
    precision_scores = []
    sample_students = recommender.student_resource_matrix.index[100:200] 

    for student_id in sample_students:
       # Utiliser la nouvelle fonction
       recall, precision = calculate_metrics_temporal_split(recommender, student_id, k=3)
       recall_scores.append(recall)
       precision_scores.append(precision)

    avg_recall = np.mean([r for r in recall_scores if r is not None])
    avg_precision = np.mean([p for p in precision_scores if p is not None])

    
    print(f"✅ Precision@3 moyen (Temporel) pour l'échantillon: {avg_precision:.4f}")
