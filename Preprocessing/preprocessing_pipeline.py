"""
Pipeline de Preprocessing Complet pour Dataset OULAD
====================================================
Ce script traite les données brutes OULAD et crée des features
pour la prédiction At-Risk, Quiz Performance, et Recommendations
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OULADPreprocessor:
    """
    Classe principale pour le preprocessing du dataset OULAD
    """
    
    def __init__(self, data_path='Data/raw/', output_path='Data/processed/'):
        self.data_path = data_path
        self.output_path = output_path
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_data(self):
        """Charge toutes les tables OULAD"""
        print("📥 Chargement des données OULAD...")
        
        self.student_info = pd.read_csv(f'{self.data_path}studentInfo.csv')
        self.student_assessment = pd.read_csv(f'{self.data_path}studentAssessment.csv')
        self.assessments = pd.read_csv(f'{self.data_path}assessments.csv')
        self.student_vle = pd.read_csv(f'{self.data_path}studentVle.csv')
        self.vle = pd.read_csv(f'{self.data_path}vle.csv')
        self.courses = pd.read_csv(f'{self.data_path}courses.csv')
        self.student_registration = pd.read_csv(f'{self.data_path}studentRegistration.csv')
        
        print(f"✅ Données chargées:")
        print(f"   - Étudiants: {len(self.student_info)}")
        print(f"   - Soumissions d'évaluations: {len(self.student_assessment)}")
        print(f"   - Interactions VLE: {len(self.student_vle)}")
        
    def clean_data(self):
        """Nettoyage des données manquantes et aberrantes"""
        print("\n🧹 Nettoyage des données...")
        
        # Remplacer les valeurs manquantes dans IMD_band
        self.student_info['imd_band'].fillna('Unknown', inplace=True)
        
        # Remplacer scores manquants par 0 (non soumis)
        self.student_assessment['score'].fillna(0, inplace=True)
        
        # Supprimer les doublons
        self.student_info.drop_duplicates(subset=['id_student', 'code_module', 'code_presentation'], inplace=True)
        
        # Filtrer les dates aberrantes (avant début du cours)
        self.student_assessment = self.student_assessment[self.student_assessment['date_submitted'] >= 0]
        
        print("✅ Nettoyage terminé")
        
    def create_vle_features(self):
        """Créer les features basées sur l'engagement VLE"""
        print("\n📊 Création des features VLE (engagement)...")
        
        # Agréger les interactions VLE par étudiant
        vle_agg = self.student_vle.groupby(['id_student', 'code_module', 'code_presentation']).agg({
            'sum_click': ['sum', 'mean', 'std', 'max'],
            'date': ['min', 'max', 'count']  # première/dernière interaction, nb de jours actifs
        }).reset_index()
        
        # Aplatir les colonnes multi-index
        vle_agg.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                          for col in vle_agg.columns.values]
        
        # Renommer pour clarté
        vle_agg.rename(columns={
            'sum_click_sum': 'total_clicks',
            'sum_click_mean': 'avg_clicks_per_day',
            'sum_click_std': 'std_clicks',
            'sum_click_max': 'max_clicks_day',
            'date_min': 'first_interaction_day',
            'date_max': 'last_interaction_day',
            'date_count': 'active_days'
        }, inplace=True)
        
        # Remplacer std NaN (1 seule interaction) par 0
        vle_agg['std_clicks'].fillna(0, inplace=True)
        
        # Calculer la durée d'engagement
        vle_agg['engagement_duration'] = vle_agg['last_interaction_day'] - vle_agg['first_interaction_day']
        
        # Calculer le taux d'activité (jours actifs / durée totale)
        vle_agg['activity_rate'] = vle_agg['active_days'] / (vle_agg['engagement_duration'] + 1)
        
        self.vle_features = vle_agg
        print(f"✅ Features VLE créées: {vle_agg.shape[1]-3} features pour {len(vle_agg)} étudiants")
        
        return vle_agg
    
    def create_assessment_features(self):
        """Créer les features basées sur les évaluations"""
        print("\n📝 Création des features d'évaluation...")
        
        # Merger avec info sur les assessments
        assess_merged = self.student_assessment.merge(
            self.assessments, 
            on='id_assessment'
        )
        
        # Calculer le délai de soumission (date_submitted - date de l'assessment)
        assess_merged['submission_delay'] = assess_merged['date_submitted'] - assess_merged['date']
        
        # Identifier les soumissions tardives
        assess_merged['is_late'] = (assess_merged['submission_delay'] > 0).astype(int)
        
        # Agréger par étudiant
        assessment_agg = assess_merged.groupby(['id_student', 'code_module', 'code_presentation']).agg({
            'score': ['mean', 'std', 'min', 'max', 'count'],
            'submission_delay': ['mean', 'std', 'min'],
            'is_late': 'sum',
            'weight': 'sum'  # poids total des évaluations complétées
        }).reset_index()
        
        # Aplatir colonnes
        assessment_agg.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                                 for col in assessment_agg.columns.values]
        
        # Renommer
        assessment_agg.rename(columns={
            'score_mean': 'avg_score',
            'score_std': 'std_score',
            'score_min': 'min_score',
            'score_max': 'max_score',
            'score_count': 'num_assessments_completed',
            'submission_delay_mean': 'avg_submission_delay',
            'submission_delay_std': 'std_submission_delay',
            'submission_delay_min': 'earliest_submission',
            'is_late_sum': 'num_late_submissions',
            'weight_sum': 'total_assessment_weight'
        }, inplace=True)
        
        # Remplacer std NaN par 0
        assessment_agg['std_score'].fillna(0, inplace=True)
        assessment_agg['std_submission_delay'].fillna(0, inplace=True)
        
        # Calculer le taux de soumissions tardives
        assessment_agg['late_submission_rate'] = (
            assessment_agg['num_late_submissions'] / assessment_agg['num_assessments_completed']
        )
        
        self.assessment_features = assessment_agg
        print(f"✅ Features Assessment créées: {assessment_agg.shape[1]-3} features pour {len(assessment_agg)} étudiants")
        
        return assessment_agg
    
    def create_temporal_features(self):
        """Créer des features temporelles (tendances d'engagement)"""
        print("\n⏰ Création des features temporelles...")
        
        # Diviser le semestre en périodes (début, milieu, fin)
        self.student_vle['period'] = pd.cut(
            self.student_vle['date'], 
            bins=[-np.inf, 60, 180, np.inf], 
            labels=['early', 'mid', 'late']
        )
        
        # Calculer l'engagement par période
        temporal_agg = self.student_vle.groupby(
            ['id_student', 'code_module', 'code_presentation', 'period']
        )['sum_click'].sum().unstack(fill_value=0).reset_index()
        
        temporal_agg.columns.name = None
        temporal_agg.rename(columns={
            'early': 'clicks_early_period',
            'mid': 'clicks_mid_period',
            'late': 'clicks_late_period'
        }, inplace=True)
        
        # Calculer les tendances
        temporal_agg['engagement_trend'] = (
            temporal_agg['clicks_late_period'] - temporal_agg['clicks_early_period']
        )
        
        # Déclin d'engagement (booléen)
        temporal_agg['engagement_decline'] = (
            temporal_agg['engagement_trend'] < -100
        ).astype(int)
        
        self.temporal_features = temporal_agg
        print(f"✅ Features temporelles créées pour {len(temporal_agg)} étudiants")
        
        return temporal_agg
    
    def create_resource_diversity_features(self):
        """Calculer la diversité des ressources consultées"""
        print("\n🌐 Création des features de diversité des ressources...")
        
        # Merger student_vle avec vle pour obtenir les types de ressources
        vle_with_type = self.student_vle.merge(
            self.vle[['id_site', 'activity_type']], 
            on='id_site'
        )
        
        # Compter les types de ressources uniques par étudiant
        resource_diversity = vle_with_type.groupby(
            ['id_student', 'code_module', 'code_presentation']
        )['activity_type'].nunique().reset_index()
        
        resource_diversity.rename(columns={
            'activity_type': 'num_resource_types'
        }, inplace=True)
        
        # Calculer la distribution des interactions par type de ressource
        resource_dist = vle_with_type.groupby(
            ['id_student', 'code_module', 'code_presentation', 'activity_type']
        )['sum_click'].sum().unstack(fill_value=0).reset_index()
        
        # Merger les deux
        resource_features = resource_diversity.merge(
            resource_dist, 
            on=['id_student', 'code_module', 'code_presentation']
        )
        
        self.resource_features = resource_features
        print(f"✅ Features de diversité créées: {resource_features.shape[1]-3} features")
        
        return resource_features
    
    def create_demographic_features(self):
        """Encoder les features démographiques"""
        print("\n👥 Traitement des features démographiques...")
        
        demo_features = self.student_info.copy()
        
        # Encoder les variables catégorielles
        categorical_cols = ['gender', 'region', 'highest_education', 
                           'imd_band', 'age_band', 'disability']
        
        for col in categorical_cols:
            le = LabelEncoder()
            demo_features[f'{col}_encoded'] = le.fit_transform(demo_features[col].astype(str))
            self.label_encoders[col] = le
        
        # Calculer le nombre de crédits précédents (indicateur d'expérience)
        demo_features['has_previous_credits'] = (demo_features['num_of_prev_attempts'] > 0).astype(int)
        
        # Calculer le ratio de crédits (crédits étudiés / crédits du module)
        demo_features['credit_ratio'] = demo_features['studied_credits'] / (demo_features['studied_credits'] + 1)
        
        self.demo_features = demo_features
        print(f"✅ Features démographiques encodées")
        
        return demo_features
    
    def merge_all_features(self):
        """Merger toutes les features en un seul dataset"""
        print("\n🔗 Fusion de toutes les features...")
        
        # Commencer avec les infos démographiques
        merged = self.demo_features.copy()
        
        # Merger VLE features
        merged = merged.merge(
            self.vle_features, 
            on=['id_student', 'code_module', 'code_presentation'],
            how='left'
        )
        
        # Merger Assessment features
        merged = merged.merge(
            self.assessment_features,
            on=['id_student', 'code_module', 'code_presentation'],
            how='left'
        )
        
        # Merger Temporal features
        merged = merged.merge(
            self.temporal_features,
            on=['id_student', 'code_module', 'code_presentation'],
            how='left'
        )
        
        # Merger Resource features
        merged = merged.merge(
            self.resource_features,
            on=['id_student', 'code_module', 'code_presentation'],
            how='left'
        )
        
        # Remplacer les NaN (étudiants sans interactions) par 0
        merged.fillna(0, inplace=True)
        
        self.merged_data = merged
        print(f"✅ Dataset complet créé: {merged.shape[0]} étudiants, {merged.shape[1]} features")
        
        return merged
    
    def create_target_variables(self):
        """Créer les variables cibles pour différentes prédictions"""
        print("\n🎯 Création des variables cibles...")
        
        # 1. At-Risk Target (Fail ou Withdrawn = 1, Pass = 0)
        self.merged_data['at_risk'] = self.merged_data['final_result'].apply(
            lambda x: 1 if x in ['Fail', 'Withdrawn'] else 0
        )
        
        # 2. Dropout Target (Withdrawn = 1, autres = 0)
        self.merged_data['dropout'] = (self.merged_data['final_result'] == 'Withdrawn').astype(int)
        
        # 3. Pass/Fail Target (Pass = 1, Fail = 0, exclure Withdrawn)
        self.merged_data['pass'] = self.merged_data['final_result'].apply(
            lambda x: 1 if x == 'Pass' else (0 if x == 'Fail' else np.nan)
        )
        
        # 4. Multi-class Target
        target_mapping = {'Fail': 0, 'Withdrawn': 1, 'Pass': 2, 'Distinction': 3}
        self.merged_data['result_multiclass'] = self.merged_data['final_result'].map(target_mapping)
        
        print(f"✅ Variables cibles créées:")
        print(f"   - At-Risk: {self.merged_data['at_risk'].sum()} étudiants à risque")
        print(f"   - Dropout: {self.merged_data['dropout'].sum()} abandons")
        print(f"   - Pass Rate: {self.merged_data['pass'].mean()*100:.1f}%")
        
    def create_recommendation_features(self):
        """Créer un dataset pour le système de recommandations"""
        print("\n💡 Création des features pour recommandations...")
        
        # Merger student_vle avec vle pour avoir les types de ressources
        vle_detailed = self.student_vle.merge(
            self.vle[['id_site', 'activity_type', 'week_from', 'week_to']], 
            on='id_site'
        )
        
        # Créer une matrice étudiant-ressource
        student_resource = vle_detailed.groupby(
            ['id_student', 'code_module', 'code_presentation', 'activity_type']
        )['sum_click'].sum().reset_index()
        
        # Pivot pour avoir une ligne par étudiant
        student_resource_pivot = student_resource.pivot_table(
            index=['id_student', 'code_module', 'code_presentation'],
            columns='activity_type',
            values='sum_click',
            fill_value=0
        ).reset_index()
        
        # Merger avec les résultats
        recommendation_data = student_resource_pivot.merge(
            self.student_info[['id_student', 'code_module', 'code_presentation', 'final_result']],
            on=['id_student', 'code_module', 'code_presentation']
        )
        
        self.recommendation_data = recommendation_data
        print(f"✅ Dataset recommandations créé: {recommendation_data.shape}")
        
        return recommendation_data
    
    def create_quiz_performance_features(self):
        """Créer un dataset spécifique pour la prédiction de performance aux quiz"""
        print("\n📋 Création des features pour prédiction quiz...")
        
        # Filtrer uniquement les TMA (Tutor Marked Assessment - quiz)
        quiz_data = self.student_assessment.merge(
            self.assessments[self.assessments['assessment_type'] == 'TMA'],
            on='id_assessment'
        )
        
        # Pour chaque étudiant, calculer les stats sur les quiz précédents
        quiz_features = []
        
        for (student, module, presentation), group in quiz_data.groupby(
            ['id_student', 'code_module', 'code_presentation']
        ):
            sorted_group = group.sort_values('date')
            
            for i in range(1, len(sorted_group)):
                # Features basées sur les quiz précédents
                previous_quizzes = sorted_group.iloc[:i]
                current_quiz = sorted_group.iloc[i]
                
                features = {
                    'id_student': student,
                    'code_module': module,
                    'code_presentation': presentation,
                    'id_assessment': current_quiz['id_assessment'],
                    'prev_avg_score': previous_quizzes['score'].mean(),
                    'prev_std_score': previous_quizzes['score'].std(),
                    'prev_min_score': previous_quizzes['score'].min(),
                    'prev_max_score': previous_quizzes['score'].max(),
                    'num_prev_quizzes': len(previous_quizzes),
                    'prev_avg_delay': (previous_quizzes['date_submitted'] - previous_quizzes['date']).mean(),
                    'trend': previous_quizzes['score'].iloc[-1] - previous_quizzes['score'].iloc[0] if len(previous_quizzes) > 1 else 0,
                    'actual_score': current_quiz['score']  # Target
                }
                
                quiz_features.append(features)
        
        self.quiz_performance_data = pd.DataFrame(quiz_features)
        self.quiz_performance_data.fillna(0, inplace=True)
        
        print(f"✅ Dataset quiz performance créé: {len(self.quiz_performance_data)} enregistrements")
        
        return self.quiz_performance_data
    
    def normalize_features(self):
        """Normaliser les features numériques"""
        print("\n📏 Normalisation des features...")
        
        # Sélectionner les colonnes numériques à normaliser
        numeric_cols = self.merged_data.select_dtypes(include=[np.number]).columns
        
        # Exclure les IDs et les targets
        exclude_cols = ['id_student', 'at_risk', 'dropout', 'pass', 'result_multiclass',
                       'gender_encoded', 'region_encoded', 'highest_education_encoded',
                       'imd_band_encoded', 'age_band_encoded', 'disability_encoded']
        
        cols_to_normalize = [col for col in numeric_cols if col not in exclude_cols]
        
        # Normaliser
        self.merged_data[cols_to_normalize] = self.scaler.fit_transform(
            self.merged_data[cols_to_normalize]
        )
        
        print(f"✅ {len(cols_to_normalize)} features normalisées")
    
    def save_processed_data(self):
        """Sauvegarder les données preprocessed"""
        print("\n💾 Sauvegarde des données preprocessed...")
        
        # Colonnes catégorielles originales à exclure de 'at_risk_data.csv'
        original_categorical_cols = [
            'gender', 'region', 'highest_education', 
            'imd_band', 'age_band', 'disability', 'final_result',
            'code_module', 'code_presentation' # ces deux dernières sont déjà dans default_exclude du trainer
        ]
        
        # Dataset principal (At-Risk, Dropout, Pass/Fail)
        self.merged_data.to_csv(f'{self.output_path}students_features.csv', index=False)
        print(f"  ✅ students_features.csv sauvegardé ({self.merged_data.shape})")
        
        # Dataset At-Risk spécifique (doit être purement numérique)
        
        # Colonnes à conserver pour l'entraînement At-Risk (Targets + IDs + Features numériques)
        at_risk_cols_to_keep = [
            col for col in self.merged_data.columns 
            if col not in original_categorical_cols
        ]
    
        self.merged_data[at_risk_cols_to_keep].to_csv(
            f'{self.output_path}classification_data.csv', index=False
        )
        print(f"  ✅ classification_data.csv sauvegardé")
        
        
        # Dataset Quiz Performance
        if hasattr(self, 'quiz_performance_data'):
            self.quiz_performance_data.to_csv(
                f'{self.output_path}quiz_performance.csv', index=False
            )
            print(f"   ✅ quiz_performance.csv sauvegardé ({self.quiz_performance_data.shape})")
        
        # Dataset Recommendations
        if hasattr(self, 'recommendation_data'):
            self.recommendation_data.to_csv(
                f'{self.output_path}recommendations_data.csv', index=False
            )
            print(f"   ✅ recommendations_data.csv sauvegardé ({self.recommendation_data.shape})")
        
        print("\n✅ Tous les fichiers sauvegardés dans:", self.output_path)
    
    def run_full_pipeline(self):
        """Exécuter le pipeline complet de preprocessing"""
        print("="*60)
        print("🚀 DÉMARRAGE DU PIPELINE DE PREPROCESSING OULAD")
        print("="*60)
        
        # 1. Charger les données
        self.load_data()
        
        # 2. Nettoyer
        self.clean_data()
        
        # 3. Créer les features
        self.create_vle_features()
        self.create_assessment_features()
        self.create_temporal_features()
        self.create_resource_diversity_features()
        self.create_demographic_features()
        
        # 4. Merger tout
        self.merge_all_features()
        
        # 5. Créer les targets
        self.create_target_variables()
        
        # 6. Datasets spécialisés
        self.create_recommendation_features()
        self.create_quiz_performance_features()
        
        # 7. Normaliser
        self.normalize_features()
        
        # 8. Sauvegarder
        self.save_processed_data()
        
        print("\n" + "="*60)
        print("✅ PIPELINE TERMINÉ AVEC SUCCÈS!")
        print("="*60)
        print(f"\n📊 Résumé:")
        print(f"   - Total étudiants: {len(self.merged_data)}")
        print(f"   - Total features: {self.merged_data.shape[1]}")
        print(f"   - Étudiants à risque: {self.merged_data['at_risk'].sum()} ({self.merged_data['at_risk'].mean()*100:.1f}%)")
        print(f"   - Taux de réussite: {(1-self.merged_data['at_risk'].mean())*100:.1f}%")
        
        return self.merged_data


# ==========================================
# SCRIPT D'EXÉCUTION
# ==========================================

if __name__ == "__main__":
    # Initialiser le preprocessor
    preprocessor = OULADPreprocessor(
        data_path='Data/raw/',
        output_path='Data/processed/'
    )
    
    # Exécuter le pipeline complet
    processed_data = preprocessor.run_full_pipeline()
    
    print("\n🎉 Preprocessing terminé!")
