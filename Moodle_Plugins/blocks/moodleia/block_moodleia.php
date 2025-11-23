<?php
/**
 * Classe du bloc MoodleIA Dashboard.
 * Gère la logique de détermination du rôle et la récupération des données de l'API.
 */

defined('MOODLE_INTERNAL') || die();

require_once(__DIR__ . '/lib.php');

class block_moodleia extends block_base {

    /**
     * Initialisation des propriétés du bloc.
     */
    public function init() {
        $this->title = get_string('pluginname', 'block_moodleia');
    }

    /**
     * Retourne le contenu principal du bloc.
     * C'est ici que la logique de l'application est exécutée.
     */
    public function get_content() {
        // Ne rien faire si le contenu est déjà mis en cache
        if ($this->content !== null) {
            return $this->content;
        }

        global $USER, $CFG, $SESSION;
        $this->content = new stdClass();
        $this->content->text = '';
        $this->content->footer = '';

        // Déterminer le rôle de l'utilisateur
        // Simulation: l'utilisateur 1 est Admin, les autres sont Étudiants.
        $is_admin = $USER->id === 1 || is_siteadmin(); // ID 1 est souvent l'Admin dans une nouvelle installation Moodle.
        $user_id = $USER->id;

        $data = [];

        // 1. Récupérer les données spécifiques au rôle
        if ($is_admin) {
            // Un Admin a besoin de deux endpoints
            $stats = moodleia_fetch_data("/stats/global");
            $interventions = moodleia_fetch_data("/interventions/at-risk-students");

            if (isset($stats['error']) || isset($interventions['error'])) {
                $error_message = isset($stats['error']) ? $stats['error'] : $interventions['error'];
                $this->content->text = "<div class='moodleia-error'>{$error_message}</div>";
                return $this->content;
            }

            $data = ['stats' => $stats, 'interventions' => $interventions];

        } else {
            // Un étudiant a besoin de son propre tableau de bord
            $data = moodleia_fetch_data("/student/{$user_id}/dashboard");
            
            if (isset($data['error'])) {
                $this->content->text = "<div class='moodleia-error'>{$data['error']}</div>";
                return $this->content;
            }
        }

        // 2. Rendre la vue
        ob_start();
        
        // Les variables sont disponibles dans le fichier inclus.
        require(__DIR__ . '/view_moodleia.php');

        $this->content->text = ob_get_clean();

        return $this->content;
    }
    
    /**
     * Permet au bloc d'être configuré globalement.
     */
    public function has_config() {
        return true; 
    }
}