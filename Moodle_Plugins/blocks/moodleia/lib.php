<?php
/**
 * Fichier de bibliothèque pour le bloc MoodleIA.
 * Contient les fonctions utilitaires pour la démo, simulant les appels d'API et le formatage.
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Simule la récupération de données depuis une API externe.
 *
 * @param string $endpoint L'endpoint de l'API à appeler.
 * @return array Les données simulées de l'API ou un tableau contenant une clé 'error'.
 */
function moodleia_fetch_data(string $endpoint): array {
    global $USER;
    $user_id = $USER->id;

    // Simulation de données spécifiques à l'Admin
    if ($endpoint === "/stats/global") {
        return [
            'total_students' => 450,
            'at_risk_count' => 35,
            'at_risk_percentage' => 7.8, // 7.8% (utilisé pour calculer le pourcentage affiché)
            'avg_score' => 81.5,
            'avg_engagement_days' => 4.2
        ];
    }

    if ($endpoint === "/interventions/at-risk-students") {
        return [
            'high_priority' => 12,
            'students' => [
                [
                    'student_id' => 101,
                    'risk_probability' => 0.92,
                    'priority' => 'high',
                    'recommended_actions' => ['Contacter l\'étudiant', 'Vérifier les soumissions']
                ],
                [
                    'student_id' => 105,
                    'risk_probability' => 0.85,
                    'priority' => 'high',
                    'recommended_actions' => ['Offrir un tutorat']
                ],
                [
                    'student_id' => 112,
                    'risk_probability' => 0.78,
                    'priority' => 'medium',
                    'recommended_actions' => ['Envoyer un rappel de module']
                ],
                [
                    'student_id' => 120,
                    'risk_probability' => 0.71,
                    'priority' => 'medium',
                    'recommended_actions' => ['Vérifier l\'activité']
                ],
            ]
        ];
    }

    // Simulation de données spécifiques à l'Étudiant (Dashboard personnel)
    if (preg_match("/^\/student\/(\d+)\/dashboard$/", $endpoint, $matches)) {
        // Simuler des données différentes pour Admin (ID 1) et d'autres étudiants (par exemple, ID 2 en risque)
        $is_at_risk = $user_id === 2 || $user_id === 105;
        $risk_prob = $is_at_risk ? 0.88 : 0.25;

        return [
            'predictions' => [
                'at_risk' => [
                    'is_at_risk' => $is_at_risk,
                    'risk_probability' => $risk_prob,
                ],
                'dropout' => [
                    'dropout_probability' => $risk_prob * 0.7, // Risque d'abandon légèrement inférieur
                ]
            ],
            'performance' => [
                'avg_score' => $is_at_risk ? 55 : 88,
                'active_days' => $is_at_risk ? 1.5 : 5.8,
                'late_submission_rate' => $is_at_risk ? 40 : 5,
            ],
            'insights' => [
                'engagement_level' => $is_at_risk ? 'Faible' : 'Élevé',
            ],
            'alerts' => $is_at_risk ? [
                [
                    'level' => 'high',
                    'type' => 'Devoir Manqué',
                    'message' => 'L\'évaluation "Introduction à l\'IA" est manquée.',
                    'action' => 'Soumettez-la immédiatement pour éviter de perdre des points.',
                ],
                [
                    'level' => 'medium',
                    'type' => 'Faible Engagement',
                    'message' => 'Moins de 2 jours d\'activité cette semaine.',
                    'action' => 'Consultez les dernières ressources et participez au forum.',
                ],
            ] : [
                [
                    'level' => 'low',
                    'type' => 'Bon Progrès',
                    'message' => 'Félicitations pour votre engagement constant.',
                    'action' => 'Continuez à réviser le Module 3.',
                ],
            ],
            'recommendations' => $is_at_risk ? [
                ['type' => 'Vidéo', 'resource_name' => 'Révision rapide du Module 1', 'score' => 0.95],
                ['type' => 'Quiz', 'resource_name' => 'Quiz de pratique pour le Chapitre 2', 'score' => 0.88],
            ] : [
                ['type' => 'Article', 'resource_name' => 'Approfondissement : l\'apprentissage par renforcement', 'score' => 0.99],
                ['type' => 'Forum', 'resource_name' => 'Défis avancés de l\'IA', 'score' => 0.92],
            ]
        ];
    }

    return ['error' => "Endpoint inconnu ou données non disponibles pour l'utilisateur {$user_id}. Simulez une défaillance de l'API."];
}

/**
 * Formate une probabilité (de 0.0 à 1.0) en pourcentage arrondi sans décimales.
 *
 * @param float $proba La probabilité (entre 0 et 1).
 * @return string La chaîne de pourcentage formatée.
 */
function moodleia_format_proba(float $proba): string {
    return number_format($proba * 100, 0) . '%';
}