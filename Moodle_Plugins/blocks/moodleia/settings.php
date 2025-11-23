<?php
    /**
     * Fichier de définition des paramètres d'administration pour le bloc MoodleIA.
     */

    defined('MOODLE_INTERNAL') || die();

    if ($ADMIN->fulltree) {
        $settings->add(new admin_setting_heading(
            'block_moodleia/general',
            get_string('pluginname', 'block_moodleia'),
            get_string('moodleia_settings', 'block_moodleia')
        ));

        // Paramètre: Clé d'API (stockée cryptée si possible)
        $settings->add(new admin_setting_configtext(
            'block_moodleia/api_key',
            get_string('api_key_setting', 'block_moodleia'),
            get_string('api_key_setting_desc', 'block_moodleia'),
            '',
            PARAM_TEXT
        ));

        // Paramètre: Seuil de risque pour l'intervention
        $settings->add(new admin_setting_configtext(
            'block_moodleia/intervention_threshold',
            get_string('intervention_threshold', 'block_moodleia'),
            get_string('intervention_threshold_desc', 'block_moodleia'),
            '70', // Valeur par défaut
            PARAM_INT
        ));
    }