"""
train_all_models.py
Pipeline d'Entraînement Multi-Modèles pour OULAD
================================================
Compare plusieurs algorithmes ML et sauvegarde le meilleur modèle
pour chaque tâche de prédiction.
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, roc_auc_score, confusion_matrix,
                             mean_squared_error, mean_absolute_error, r2_score)

# ML Models
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, GradientBoostingClassifier,
                              AdaBoostClassifier, RandomForestRegressor,
                              GradientBoostingRegressor)
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
# Utilisation de try/except pour CatBoost pour les environnements sans l'installation
try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    print("CatBoost non trouvé. Les modèles CatBoost seront ignorés.")
    CATBOOST_AVAILABLE = False


# Imbalanced data handling
from imblearn.over_sampling import SMOTE
# from imblearn.under_sampling import RandomUnderSampler # Non utilisé dans la version finale
from imblearn.pipeline import Pipeline as ImbPipeline


class MultiModelTrainer:
    """
    Classe pour entraîner et comparer plusieurs modèles ML
    """
    
    def __init__(self, data_path='Data/processed/', models_path='Predictions/models/'):
        self.data_path = data_path
        self.models_path = models_path
        self.results = {}
        # Assurer que le répertoire des modèles existe
        os.makedirs(self.models_path, exist_ok=True)
        
    def load_data(self, filename):
        """Charger les données preprocessed"""
        file_full_path = f'{self.data_path}{filename}'
        if not os.path.exists(file_full_path):
            raise FileNotFoundError(f"Le fichier de données '{file_full_path}' est introuvable. Assurez-vous d'avoir exécuté la phase de preprocessing.")
            
        print(f"📥 Chargement de {filename}...")
        data = pd.read_csv(file_full_path)
        print(f"✅ Données chargées: {data.shape}")
        return data
    
    def prepare_features(self, data, target_col, exclude_cols=None):
        """Préparer X et y pour l'entraînement"""
        if target_col not in data.columns:
          raise KeyError(f"La colonne cible '{target_col}' est introuvable dans les données. Colonnes disponibles: {list(data.columns)}")
        
        if exclude_cols is None:
            exclude_cols = []
        
        # Colonnes à exclure par défaut
        default_exclude = ['id_student', 'code_module', 'code_presentation', 
                           'final_result', target_col]
        exclude_cols.extend(default_exclude)
        exclude_cols = list(set(exclude_cols))
        
        # Sélectionner les features
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        
        X = data[feature_cols]
        y = data[target_col]
        
        # Supprimer les NaN dans y
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]
        
        # Gérer les colonnes avec trop de valeurs manquantes (si elles n'ont pas été gérées au preprocessing)
        X = X.fillna(X.median())
        
        print(f"✅ Features préparées: {X.shape[1]} features, {len(y)} échantillons")
        if y.dtype in [int, float] and len(y.unique()) > 20: # Régression
             print(f"    Cible (Régression): Moy={y.mean():.2f}, Std={y.std():.2f}")
        else: # Classification
             print(f"    Distribution de la cible: {y.value_counts().to_dict()}")
        
        return X, y, feature_cols
    
    def get_classification_models(self, use_pipeline=False):
        """Retourner un dictionnaire de modèles de classification"""
        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'XGBoost': XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss'),
            'LightGBM': LGBMClassifier(n_estimators=100, random_state=42, verbose=-1),
            'AdaBoost': AdaBoostClassifier(n_estimators=100, random_state=42),
            'SVM': SVC(probability=True, random_state=42),
            'KNN': KNeighborsClassifier(n_neighbors=5),
            'Naive Bayes': GaussianNB()
        }
        
        if CATBOOST_AVAILABLE:
            models['CatBoost'] = CatBoostClassifier(iterations=100, random_state=42, verbose=False)
            
        if use_pipeline:
            # Encapsuler le modèle dans un pipeline SMOTE pour la gestion des déséquilibres
            # Cela garantit que le cross-validation et l'entraînement sont robustes
            smote = SMOTE(random_state=42)
            pipelined_models = {}
            for name, model in models.items():
                # GaussianNB ne supporte pas toujours predict_proba correctement avec les pipelines,
                # mais le wrapping dans le pipeline imblearn est la bonne approche
                pipelined_models[name] = ImbPipeline(steps=[('smote', smote), (name, model)])
            return pipelined_models
        
        return models
    
    def get_regression_models(self):
        """Retourner un dictionnaire de modèles de régression"""
        models = {
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'XGBoost': XGBRegressor(n_estimators=100, random_state=42),
            'LightGBM': LGBMRegressor(n_estimators=100, random_state=42, verbose=-1),
        }
        if CATBOOST_AVAILABLE:
            models['CatBoost'] = CatBoostRegressor(iterations=100, random_state=42, verbose=False)
        return models
    
    def evaluate_classification_model(self, model, X_train, X_test, y_train, y_test, model_name):
        """Évaluer un modèle de classification"""
        # Entraînement
        start_time = datetime.now()
        model.fit(X_train, y_train)
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Prédictions
        y_pred = model.predict(X_test)
        
        # Tenter d'obtenir les probabilités pour ROC-AUC
        y_pred_proba = None
        if hasattr(model, 'predict_proba') and model.predict_proba(X_test).shape[1] > 1:
            # Gérer le cas où le modèle est dans un pipeline SMOTE
            final_estimator = model.named_steps[model_name] if isinstance(model, ImbPipeline) else model
            
            # Pour CatBoost, il faut s'assurer d'avoir les bonnes probabilités (classe 1)
            if hasattr(final_estimator, 'predict_proba'):
                 y_pred_proba = final_estimator.predict_proba(X_test)[:, 1]
            # Sauf pour GaussianNB et autres modèles simples directement dans le pipeline
            elif hasattr(model, 'predict_proba'):
                 y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Métriques
        metrics = {
            'model_name': model_name,
            'accuracy': accuracy_score(y_test, y_pred),
            # Utilisation de zero_division=0 pour éviter les warnings
            'precision': precision_score(y_test, y_pred, average='binary', zero_division=0), 
            'recall': recall_score(y_test, y_pred, average='binary', zero_division=0),
            'f1_score': f1_score(y_test, y_pred, average='binary', zero_division=0),
            'training_time': training_time
        }
        
        if y_pred_proba is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
            except ValueError:
                metrics['roc_auc'] = 0.0 # Cas où une seule classe est présente dans y_test (rare mais possible)
        else:
             metrics['roc_auc'] = 0.0
        
        # Cross-validation
        try:
             # Le pipeline ImbPipeline gère le resample pour chaque pli de CV
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1', n_jobs=-1)
            metrics['cv_f1_mean'] = cv_scores.mean()
            metrics['cv_f1_std'] = cv_scores.std()
        except Exception:
            metrics['cv_f1_mean'] = np.nan
            metrics['cv_f1_std'] = np.nan
        
        # Matrice de confusion
        cm = confusion_matrix(y_test, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        return metrics, model
    
    def evaluate_regression_model(self, model, X_train, X_test, y_train, y_test, model_name):
        """Évaluer un modèle de régression"""
        # Entraînement
        start_time = datetime.now()
        model.fit(X_train, y_train)
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Prédictions
        y_pred = model.predict(X_test)
        
        # Métriques
        metrics = {
            'model_name': model_name,
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2_score': r2_score(y_test, y_pred),
            'training_time': training_time
        }
        
        # Cross-validation
        try:
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)
            metrics['cv_mse_mean'] = -cv_scores.mean()
            metrics['cv_mse_std'] = cv_scores.std()
        except Exception:
            metrics['cv_mse_mean'] = np.nan
            metrics['cv_mse_std'] = np.nan
        
        return metrics, model
    
    def train_at_risk_models(self):
        """Entraîner des modèles pour prédire les étudiants à risque (Classification)"""
        print("\n" + "="*70)
        print("🎯 ENTRAÎNEMENT DES MODÈLES AT-RISK (Classification)")
        print("="*70)
        
        # Charger les données
        data = self.load_data('at_risk_data.csv')
        
        # Préparer les features
        X, y, feature_cols = self.prepare_features(
            data, 
            target_col='at_risk',
            exclude_cols=['dropout', 'pass', 'result_multiclass']
        )
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📊 Distribution:")
        print(f"    Train: {len(y_train)} échantillons")
        print(f"    Test: {len(y_test)} échantillons")
        print(f"    At-Risk rate: {y.mean()*100:.1f}%")
        
        # Obtenir les modèles avec le pipeline SMOTE intégré
        models = self.get_classification_models(use_pipeline=True)
        
        # Entraîner et évaluer chaque modèle
        results = []
        trained_models = {}
        
        print("\n🔄 Entraînement des modèles (avec SMOTE dans le pipeline)...\n")
        
        for name, model in models.items():
            print(f"    🔹 {name}...", end=" ")
            try:
                metrics, trained_model = self.evaluate_classification_model(
                    model, X_train, X_test, y_train, y_test, name
                )
                results.append(metrics)
                trained_models[name] = trained_model
                print(f"✅ F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")
        
        # Créer un DataFrame des résultats
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('f1_score', ascending=False)
        
        print("\n" + "="*70)
        print("📊 RÉSULTATS COMPARATIFS AT-RISK (triés par F1-Score)")
        print("="*70)
        print(results_df[['model_name', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'cv_f1_mean']].to_string(index=False))
        
        # Sélectionner le meilleur modèle
        best_model_name = results_df.iloc[0]['model_name']
        best_model = trained_models[best_model_name]
        best_metrics = results_df.iloc[0].to_dict()
        
        print(f"\n🏆 MEILLEUR MODÈLE AT-RISK: {best_model_name}")
        print(f"    F1-Score: {best_metrics['f1_score']:.4f}")
        print(f"    ROC-AUC: {best_metrics['roc_auc']:.4f}")
        
        # Sauvegarder le meilleur modèle
        model_info = {
            'model': best_model,
            'model_name': best_model_name,
            'feature_columns': feature_cols,
            'metrics': best_metrics,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'task': 'at_risk_prediction'
        }
        
        joblib.dump(model_info, f'{self.models_path}at_risk_model.pkl')
        print(f"\n💾 Modèle sauvegardé: {self.models_path}at_risk_model.pkl")
        
        # Sauvegarder les résultats comparatifs
        results_df.to_csv(f'{self.models_path}at_risk_comparison.csv', index=False)
        print(f"💾 Comparaison sauvegardée: {self.models_path}at_risk_comparison.csv")
        
        self.results['at_risk'] = results_df
        
        return best_model, results_df
    
    def train_quiz_performance_models(self):
        """Entraîner des modèles pour prédire la performance aux quiz (Régression)"""
        print("\n" + "="*70)
        print("📝 ENTRAÎNEMENT DES MODÈLES QUIZ PERFORMANCE (Régression)")
        print("="*70)
        
        # Charger les données
        data = self.load_data('quiz_performance.csv')
        
        # Préparer les features
        X, y, feature_cols = self.prepare_features(
            data, 
            target_col='actual_score',
            exclude_cols=['id_assessment']
        )
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"\n📊 Distribution:")
        print(f"    Train: {len(y_train)} échantillons")
        print(f"    Test: {len(y_test)} échantillons")
        print(f"    Score moyen: {y.mean():.2f}")
        
        # Obtenir les modèles de régression
        models = self.get_regression_models()
        
        # Entraîner et évaluer chaque modèle
        results = []
        trained_models = {}
        
        print("\n🔄 Entraînement des modèles...\n")
        
        for name, model in models.items():
            print(f"    🔹 {name}...", end=" ")
            try:
                metrics, trained_model = self.evaluate_regression_model(
                    model, X_train, X_test, y_train, y_test, name
                )
                results.append(metrics)
                trained_models[name] = trained_model
                print(f"✅ RMSE: {metrics['rmse']:.4f}, R²: {metrics['r2_score']:.4f}")
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")
        
        # Créer un DataFrame des résultats
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('r2_score', ascending=False)
        
        print("\n" + "="*70)
        print("📊 RÉSULTATS COMPARATIFS QUIZ PERFORMANCE (triés par R²)")
        print("="*70)
        print(results_df[['model_name', 'rmse', 'mae', 'r2_score', 'cv_mse_mean']].to_string(index=False))
        
        # Sélectionner le meilleur modèle
        best_model_name = results_df.iloc[0]['model_name']
        best_model = trained_models[best_model_name]
        best_metrics = results_df.iloc[0].to_dict()
        
        print(f"\n🏆 MEILLEUR MODÈLE QUIZ PERFORMANCE: {best_model_name}")
        print(f"    R²: {best_metrics['r2_score']:.4f}")
        print(f"    RMSE: {best_metrics['rmse']:.4f}")
        
        # Sauvegarder le meilleur modèle
        model_info = {
            'model': best_model,
            'model_name': best_model_name,
            'feature_columns': feature_cols,
            'metrics': best_metrics,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'task': 'quiz_performance_prediction'
        }
        
        joblib.dump(model_info, f'{self.models_path}quiz_performance_model.pkl')
        print(f"\n💾 Modèle sauvegardé: {self.models_path}quiz_performance_model.pkl")
        
        # Sauvegarder les résultats comparatifs
        results_df.to_csv(f'{self.models_path}quiz_performance_comparison.csv', index=False)
        print(f"💾 Comparaison sauvegardée: {self.models_path}quiz_performance_comparison.csv")
        
        self.results['quiz_performance'] = results_df
        
        return best_model, results_df
    
    def train_dropout_models(self):
        """Entraîner des modèles pour prédire l'abandon (dropout) (Classification)"""
        print("\n" + "="*70)
        print("🚪 ENTRAÎNEMENT DES MODÈLES DROPOUT PREDICTION (Classification)")
        print("="*70)
        
        # Charger les données
        data = self.load_data('at_risk_data.csv')
        
        # Préparer les features
        X, y, feature_cols = self.prepare_features(
            data, 
            target_col='dropout',
            exclude_cols=['at_risk', 'pass', 'result_multiclass']
        )
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📊 Distribution:")
        print(f"    Train: {len(y_train)} échantillons")
        print(f"    Test: {len(y_test)} échantillons")
        print(f"    Dropout rate: {y.mean()*100:.1f}%")
        
        # Obtenir les modèles avec le pipeline SMOTE intégré
        models = self.get_classification_models(use_pipeline=True)
        
        # Entraîner et évaluer chaque modèle
        results = []
        trained_models = {}
        
        print("\n🔄 Entraînement des modèles (avec SMOTE dans le pipeline)...\n")
        
        for name, model in models.items():
            print(f"    🔹 {name}...", end=" ")
            try:
                metrics, trained_model = self.evaluate_classification_model(
                    model, X_train, X_test, y_train, y_test, name
                )
                results.append(metrics)
                trained_models[name] = trained_model
                print(f"✅ F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")
        
        # Créer un DataFrame des résultats
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('f1_score', ascending=False)
        
        print("\n" + "="*70)
        print("📊 RÉSULTATS COMPARATIFS DROPOUT (triés par F1-Score)")
        print("="*70)
        print(results_df[['model_name', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'cv_f1_mean']].to_string(index=False))
        
        # Sélectionner le meilleur modèle
        best_model_name = results_df.iloc[0]['model_name']
        best_model = trained_models[best_model_name]
        best_metrics = results_df.iloc[0].to_dict()
        
        print(f"\n🏆 MEILLEUR MODÈLE DROPOUT: {best_model_name}")
        print(f"    F1-Score: {best_metrics['f1_score']:.4f}")
        print(f"    ROC-AUC: {best_metrics['roc_auc']:.4f}")
        
        # Sauvegarder le meilleur modèle
        model_info = {
            'model': best_model,
            'model_name': best_model_name,
            'feature_columns': feature_cols,
            'metrics': best_metrics,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'task': 'dropout_prediction'
        }
        
        joblib.dump(model_info, f'{self.models_path}dropout_model.pkl')
        print(f"\n💾 Modèle sauvegardé: {self.models_path}dropout_model.pkl")
        
        results_df.to_csv(f'{self.models_path}dropout_comparison.csv', index=False)
        print(f"💾 Comparaison sauvegardée: {self.models_path}dropout_comparison.csv")
        
        self.results['dropout'] = results_df
        
        return best_model, results_df
    
    def train_pass_fail_models(self):
        """Entraîner des modèles pour prédire Pass/Fail (excluant Withdrawn) (Classification)"""
        print("\n" + "="*70)
        print("✅❌ ENTRAÎNEMENT DES MODÈLES PASS/FAIL (Classification)")
        print("="*70)
        
        # Charger les données
        data = self.load_data('classification_data.csv')
        
        # Préparer les features
        X, y, feature_cols = self.prepare_features(
            data, 
            target_col='pass',
            exclude_cols=['at_risk', 'dropout', 'result_multiclass']
        )
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📊 Distribution:")
        print(f"    Train: {len(y_train)} échantillons")
        print(f"    Test: {len(y_test)} échantillons")
        print(f"    Pass rate: {y.mean()*100:.1f}%")
        
        # Obtenir les modèles (pas de pipeline SMOTE ici car les classes sont plus équilibrées
        # après exclusion des 'Withdrawn', mais on pourrait l'ajouter si les classes étaient déséquilibrées)
        # On utilise le pipeline pour une cohérence si besoin de l'équilibrage plus tard.
        models = self.get_classification_models(use_pipeline=True)
        
        # Entraîner et évaluer chaque modèle
        results = []
        trained_models = {}
        
        print("\n🔄 Entraînement des modèles (avec SMOTE dans le pipeline)...\n")
        
        for name, model in models.items():
            print(f"    🔹 {name}...", end=" ")
            try:
                metrics, trained_model = self.evaluate_classification_model(
                    model, X_train, X_test, y_train, y_test, name
                )
                results.append(metrics)
                trained_models[name] = trained_model
                print(f"✅ F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")
        
        # Créer un DataFrame des résultats
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('f1_score', ascending=False)
        
        print("\n" + "="*70)
        print("📊 RÉSULTATS COMPARATIFS PASS/FAIL (triés par F1-Score)")
        print("="*70)
        print(results_df[['model_name', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'cv_f1_mean']].to_string(index=False))
        
        # Sélectionner le meilleur modèle
        best_model_name = results_df.iloc[0]['model_name']
        best_model = trained_models[best_model_name]
        best_metrics = results_df.iloc[0].to_dict()
        
        print(f"\n🏆 MEILLEUR MODÈLE PASS/FAIL: {best_model_name}")
        print(f"    F1-Score: {best_metrics['f1_score']:.4f}")
        print(f"    ROC-AUC: {best_metrics['roc_auc']:.4f}")
        
        # Sauvegarder le meilleur modèle
        model_info = {
            'model': best_model,
            'model_name': best_model_name,
            'feature_columns': feature_cols,
            'metrics': best_metrics,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'task': 'pass_fail_prediction'
        }
        
        joblib.dump(model_info, f'{self.models_path}pass_fail_model.pkl')
        print(f"\n💾 Modèle sauvegardé: {self.models_path}pass_fail_model.pkl")
        
        results_df.to_csv(f'{self.models_path}pass_fail_comparison.csv', index=False)
        print(f"💾 Comparaison sauvegardée: {self.models_path}pass_fail_comparison.csv")
        
        self.results['pass_fail'] = results_df
        
        return best_model, results_df
    
    def run_all_training(self):
        """Exécuter l'entraînement de tous les modèles"""
        print("\n" + "="*70)
        print("🚀 DÉMARRAGE DE L'ENTRAÎNEMENT DE TOUS LES MODÈLES")
        print("="*70)
        
        # 1. At-Risk Prediction
        try:
            self.train_at_risk_models()
        except FileNotFoundError as e:
            print(f"⚠️ Ignoré: {e}")
        
        # 2. Quiz Performance Prediction
        try:
            self.train_quiz_performance_models()
        except FileNotFoundError as e:
            print(f"⚠️ Ignoré: {e}")
        
        # 3. Dropout Prediction
        try:
            self.train_dropout_models()
        except FileNotFoundError as e:
            print(f"⚠️ Ignoré: {e}")
        
        # 4. Pass/Fail Prediction
        try:
            self.train_pass_fail_models()
        except FileNotFoundError as e:
            print(f"⚠️ Ignoré: {e}")
        
        print("\n" + "="*70)
        print("✅ TOUS LES MODÈLES ONT ÉTÉ ENTRAÎNÉS AVEC SUCCÈS!")
        print("="*70)
        
        # Résumé
        print("\n📊 RÉSUMÉ DES MEILLEURS MODÈLES:")
        print("-" * 70)
        if self.results:
            for task, results_df in self.results.items():
                best = results_df.iloc[0]
                print(f"\n🎯 **{task.upper().replace('_', ' ')}**:")
                print(f"    Modèle: **{best['model_name']}**")
                if 'f1_score' in best:
                    print(f"    F1-Score: {best['f1_score']:.4f}")
                    print(f"    ROC-AUC: {best['roc_auc']:.4f}")
                else:
                    print(f"    R²: {best['r2_score']:.4f}")
                    print(f"    RMSE: {best['rmse']:.4f}")
        else:
             print("Aucun modèle n'a pu être entraîné (problèmes de fichiers de données?).")

        print("\n" + "="*70)
        print("📦 Modèles sauvegardés dans:", self.models_path)
        print("="*70)


# ==========================================
# SCRIPT D'EXÉCUTION
# ==========================================

if __name__ == "__main__":
    # Initialiser le trainer
    trainer = MultiModelTrainer(
        data_path='Data/processed/',
        models_path='Predictions/models/'
    )
    
    # Entraîner tous les modèles
    trainer.run_all_training()
    # trainer.train_pass_fail_models()
    print("\n🎉 Entraînement terminé! Vous pouvez maintenant:")
