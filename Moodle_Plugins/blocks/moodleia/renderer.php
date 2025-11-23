<?php
/**
 * Classe de rendu pour le bloc MoodleIA.
 * Elle se charge de passer les données au template (view_moodleia.php).
 */

defined('MOODLE_INTERNAL') || die();

class block_moodleia_renderer extends plugin_renderer_base {

    /**
     * Rend le tableau de bord Administrateur ou Étudiant.
     * C'est la fonction appelée par block_moodleia::get_content().
     *
     * @param array $data Les données simulées ou réelles à afficher.
     * @param string $user_id L'ID de l'utilisateur actuel.
     * @param bool $is_admin Indique si l'utilisateur est un administrateur.
     * @return string Le HTML rendu.
     */
    public function render_moodleia_dashboard(array $data, string $user_id, bool $is_admin) {
        // La fonction moodleia_format_proba est incluse dans view_moodleia.php,
        // mais nous devons la définir ici pour les tests si besoin.
        // Puisque nous l'avons définie dans lib.php, nous allons l'inclure ici aussi si elle n'est pas déjà là.
        if (!function_exists('moodleia_format_proba') && file_exists(__DIR__ . '/lib.php')) {
            require_once(__DIR__ . '/lib.php');
        }
        $format_proba = 'moodleia_format_proba';

        // Définit les variables qui seront accessibles dans le template (view_moodleia.php)
        $output_variables = [
            'data' => $data,
            'user_id' => $user_id,
            'is_admin' => $is_admin,
            'format_proba' => $format_proba,
        ];

        // Capture le contenu généré par le template
        return $this->render_from_template('block_moodleia/view_moodleia', $output_variables);
    }
}