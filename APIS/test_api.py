"""
Script de Test pour l'API MoodleIA
===================================
Teste tous les endpoints de l'API
"""

import requests
import json
import time
from colorama import init, Fore, Style

# Initialiser colorama pour les couleurs
init()

BASE_URL = "http://localhost:5000"
TEST_STUDENT_ID = 30268  # <-- ID ÉTUDIANT MIS À JOUR
TIMEOUT = 30 # Augmenter le timeout pour les tests longs (Batch, Interventions)

def print_header(text):
    """Afficher un en-tête"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Style.RESET_ALL}\n")

def print_success(text):
    """Afficher un succès"""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    """Afficher une erreur"""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    """Afficher une info"""
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")

def test_endpoint(name, method, url, data=None, params=None):
    """Tester un endpoint"""
    print(f"\n{Fore.BLUE}🔍 Test: {name}{Style.RESET_ALL}")
    print(f"    {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        
        if response.status_code == 200:
            print_success(f"Statut: {response.status_code} OK")
            result = response.json()
            # Afficher seulement le début de la réponse pour ne pas surcharger
            print(f"    Réponse: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
            return True, result
        else:
            print_error(f"Statut: {response.status_code}")
            print(f"    Erreur: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print_error("Impossible de se connecter à l'API")
        print_info("Vérifiez que l'API est lancée : python app.py")
        return False, None
    except requests.exceptions.ReadTimeout:
        print_error(f"Erreur: Le délai de lecture ({TIMEOUT}s) a été dépassé. Le traitement est trop long.")
        return False, None
    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False, None

def run_all_tests():
    """Exécuter tous les tests"""
    
    print_header("🧪 TESTS DE L'API MOODLEIA")
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # Test 1: Health Check
    print_header("1. HEALTH CHECK")
    success, _ = test_endpoint(
        "Health Check",
        "GET",
        f"{BASE_URL}/api/health"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 2: Informations API
    print_header("2. INFORMATIONS API")
    success, _ = test_endpoint(
        "Home",
        "GET",
        f"{BASE_URL}/"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 3: Dashboard Étudiant
    print_header("3. DASHBOARD ÉTUDIANT")
    success, dashboard = test_endpoint(
        "Student Dashboard",
        "GET",
        f"{BASE_URL}/api/student/{TEST_STUDENT_ID}/dashboard"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        print_info(f"Score moyen: {dashboard.get('performance', {}).get('avg_score', 'N/A')}")
        print_info(f"Statut: {dashboard.get('predictions', {}).get('at_risk', {}).get('status', 'N/A')}")
        print_info(f"Alertes: {len(dashboard.get('alerts', []))}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 4: Prédiction At-Risk
    print_header("4. PRÉDICTION AT-RISK")
    success, at_risk = test_endpoint(
        "At-Risk Prediction",
        "GET",
        f"{BASE_URL}/api/student/{TEST_STUDENT_ID}/at-risk"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        pred = at_risk.get('prediction', {})
        print_info(f"À risque: {pred.get('is_at_risk', 'N/A')}")
        print_info(f"Probabilité: {pred.get('risk_probability', 0):.1%}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 5: Prédiction Dropout
    print_header("5. PRÉDICTION DROPOUT")
    success, dropout = test_endpoint(
        "Dropout Prediction",
        "GET",
        f"{BASE_URL}/api/student/{TEST_STUDENT_ID}/dropout"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        pred = dropout.get('prediction', {})
        print_info(f"Va abandonner: {pred.get('will_dropout', 'N/A')}")
        print_info(f"Probabilité: {pred.get('dropout_probability', 0):.1%}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 6: Recommandations
    print_header("6. RECOMMANDATIONS")
    success, recs = test_endpoint(
        "Recommendations",
        "GET",
        f"{BASE_URL}/api/student/{TEST_STUDENT_ID}/recommendations",
        params={'n': 3}
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        recommendations = recs.get('recommendations', [])
        print_info(f"Nombre de recommandations: {len(recommendations)}")
        if recommendations:
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"    {i}. {rec.get('resource_type', 'N/A')}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 7: Chatbot
    print_header("7. CHATBOT IA")
    success, chat = test_endpoint(
        "Chatbot Chat",
        "POST",
        f"{BASE_URL}/api/chatbot/chat",
        data={
            'student_id': TEST_STUDENT_ID,
            'message': 'Bonjour, comment vont mes études?'
        }
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        print_info(f"Réponse du bot: {chat.get('bot_response', 'N/A')[:100]}...")
    else:
        results['failed'] += 1
    
    time.sleep(2)  # Attendre un peu pour le chatbot
    
    # Test 8: Insights Chatbot
    print_header("8. INSIGHTS DÉTAILLÉS")
    success, insights = test_endpoint(
        "Chatbot Insights",
        "GET",
        f"{BASE_URL}/api/chatbot/insights/{TEST_STUDENT_ID}"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        insight_data = insights.get('insights', {})
        print_info(f"Niveau de risque: {insight_data.get('risk_level', 'N/A')}")
        print_info(f"Recommandations: {len(insight_data.get('recommendations', []))}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 9: Prédiction Quiz
    print_header("9. PRÉDICTION QUIZ")
    success, quiz = test_endpoint(
        "Quiz Prediction",
        "POST",
        f"{BASE_URL}/api/student/{TEST_STUDENT_ID}/quiz-prediction",
        data={
            'prev_avg_score': 65.0,
            'prev_std_score': 10.0,
            'num_prev_quizzes': 3,
            'prev_avg_delay': -2.0,
            'trend': 5.0
        }
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        print_info(f"Score prédit: {quiz.get('predicted_score', 'N/A'):.1f}/100")
        print_info(f"Recommandation: {quiz.get('recommendation', 'N/A')}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 10: Batch Predictions
    print_header("10. PRÉDICTIONS PAR LOT")
    # Utiliser un petit échantillon d'IDs valides pour le test
    batch_ids = [TEST_STUDENT_ID, TEST_STUDENT_ID + 1, TEST_STUDENT_ID + 2] 
    success, batch = test_endpoint(
        "Batch At-Risk",
        "POST",
        f"{BASE_URL}/api/batch/at-risk",
        data={'student_ids': batch_ids}
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        print_info(f"Étudiants traités: {batch.get('total_students', 0)}")
        print_info(f"À risque: {batch.get('at_risk_count', 0)}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 11: Interventions
    print_header("11. SYSTÈME D'INTERVENTION")
    success, interventions = test_endpoint(
        "At-Risk Students for Intervention",
        "GET",
        f"{BASE_URL}/api/interventions/at-risk-students",
        params={'threshold': 0.7}
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        print_info(f"Total à risque: {interventions.get('total_at_risk', 0)}")
        print_info(f"Haute priorité: {interventions.get('high_priority', 0)}")
    else:
        results['failed'] += 1
    
    time.sleep(0.5)
    
    # Test 12: Statistiques Globales
    print_header("12. STATISTIQUES GLOBALES")
    success, stats = test_endpoint(
        "Global Statistics",
        "GET",
        f"{BASE_URL}/api/stats/global"
    )
    results['total'] += 1
    if success:
        results['passed'] += 1
        print_info(f"Total étudiants: {stats.get('total_students', 0)}")
        print_info(f"% à risque: {stats.get('at_risk_percentage', 0):.1f}%")
        print_info(f"Score moyen: {stats.get('avg_score', 0):.1f}")
    else:
        results['failed'] += 1
    
    # Résumé
    print_header("📊 RÉSUMÉ DES TESTS")
    print(f"Total: {results['total']}")
    print_success(f"Réussis: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Échoués: {results['failed']}")
    
    success_rate = (results['passed'] / results['total']) * 100
    print(f"\n{Fore.CYAN}Taux de réussite: {success_rate:.1f}%{Style.RESET_ALL}")
    
    if success_rate == 100:
        print(f"\n{Fore.GREEN}{'='*70}")
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print(f"{'='*70}{Style.RESET_ALL}\n")
    elif success_rate >= 80:
        print(f"\n{Fore.YELLOW}⚠️  La plupart des tests sont passés, mais il y a quelques problèmes{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}❌ De nombreux tests ont échoué. Vérifiez la configuration{Style.RESET_ALL}\n")

if __name__ == "__main__":
    print(f"{Fore.CYAN}")
    print("="*70)
    print("🧪 SCRIPT DE TEST - API MOODLEIA")
    print("="*70)
    print(f"{Style.RESET_ALL}")
    
    print_info(f"URL de l'API: {BASE_URL}")
    print_info(f"Étudiant de test: {TEST_STUDENT_ID}")
    print_info("Assurez-vous que l'API est lancée: python app.py")
    
    input("\nAppuyez sur Entrée pour commencer les tests...")
    
    run_all_tests()
    
    print("\n✅ Tests terminés!")