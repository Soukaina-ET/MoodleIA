<?php
/**
 * Vue de rendu moderne pour les tableaux de bord Admin et Étudiant.
 * Les variables $data, $user_id, $is_admin et $format_proba doivent être définies avant l'inclusion.
 */

defined('MOODLE_INTERNAL') || die();

// Récupère la fonction utilitaire de formatage
if (!function_exists('moodleia_format_proba') && file_exists(__DIR__ . '/lib.php')) {
    require_once(__DIR__ . '/lib.php');
}
$format_proba = 'moodleia_format_proba';

if (isset($data['error'])) {
    echo "<div class='moodleia-error'><svg class='icon' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><circle cx='12' cy='12' r='10'/><line x1='12' y1='8' x2='12' y2='12'/><line x1='12' y1='16' x2='12.01' y2='16'/></svg>{$data['error']}</div>";
    return;
}
?>

<div class="moodleia-dashboard <?php echo $is_admin ? 'admin-view' : 'student-view'; ?>">

    <style>
        .moodleia-dashboard {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0;
        }
        
        .moodleia-section {
            background: #ffffff;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .moodleia-section:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        }
        
        h2 {
            color: #1e293b;
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 24px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        h3 {
            color: #334155;
            font-size: 20px;
            font-weight: 600;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Badges de statut modernes */
        .risk-high {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #dc2626;
            background: #fee2e2;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .risk-medium {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #d97706;
            background: #fef3c7;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .risk-low {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #059669;
            background: #d1fae5;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .moodleia-error {
            display: flex;
            align-items: center;
            gap: 12px;
            color: #dc2626;
            padding: 16px;
            background: #fee2e2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            font-weight: 500;
        }
        
        /* Grille de statistiques moderne */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card:nth-child(2) {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .stat-card:nth-child(3) {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .stat-card:nth-child(4) {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
        
        .stat-label {
            font-size: 13px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            margin-top: 8px;
        }
        
        /* Tableau moderne */
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 16px;
        }
        
        thead th {
            background: #f8fafc;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #e2e8f0;
        }
        
        tbody td {
            padding: 16px 12px;
            border-bottom: 1px solid #f1f5f9;
        }
        
        tbody tr {
            transition: background-color 0.2s ease;
        }
        
        tbody tr:hover {
            background-color: #f8fafc;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        tbody tr a {
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s ease;
        }
        
        tbody tr a:hover {
            color: #2563eb;
            text-decoration: underline;
        }
        
        /* Alertes modernes */
        .alerts-section ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .alerts-section li {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-high {
            background: #fef2f2;
            border-left-color: #dc2626;
        }
        
        .alert-medium {
            background: #fffbeb;
            border-left-color: #d97706;
        }
        
        .alert-low {
            background: #f0fdf4;
            border-left-color: #059669;
        }
        
        /* Performance table styling */
        .performance-section table tr td:first-child {
            color: #64748b;
            font-weight: 500;
        }
        
        .performance-section table tr td:last-child {
            font-weight: 600;
            color: #1e293b;
        }
        
        /* Recommandations */
        .recs-section ul {
            list-style: none;
            padding: 0;
        }
        
        .recs-section li {
            background: #f8fafc;
            padding: 14px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #3b82f6;
            transition: all 0.2s ease;
        }
        
        .recs-section li:hover {
            background: #eff6ff;
            transform: translateX(4px);
        }
        
        /* Badge priorité */
        .priority-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .priority-high {
            background: #fee2e2;
            color: #dc2626;
        }
        
        .priority-medium {
            background: #fef3c7;
            color: #d97706;
        }
        
        /* Icons SVG */
        .icon {
            width: 20px;
            height: 20px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .moodleia-section {
                padding: 16px;
            }
            
            h2 {
                font-size: 22px;
            }
        }
    </style>

    <?php if ($is_admin): 
    // --- Rendu du Tableau de Bord ADMINISTRATEUR ---
    $stats = $data['stats'] ?? [];
    $interventions = $data['interventions'] ?? [];
    ?>
        
        <h2>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            Tableau de bord Administrateur MoodleIA
        </h2>
        
        <!-- Statistiques Globales -->
        <div class='moodleia-section global-stats'>
            <h3>
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="16"/>
                </svg>
                Statistiques Générales
            </h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Étudiants</div>
                    <div class="stat-value"><?php echo $stats['total_students'] ?? 'N/A'; ?></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Étudiants à Risque</div>
                    <div class="stat-value"><?php echo $stats['at_risk_count'] ?? 'N/A'; ?></div>
                    <div style="font-size: 14px; margin-top: 4px; opacity: 0.9;">
                        <?php echo $format_proba($stats['at_risk_percentage'] / 100 ?? 0); ?>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Score Moyen</div>
                    <div class="stat-value"><?php echo number_format($stats['avg_score'] ?? 0, 1); ?>%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Engagement Moyen</div>
                    <div class="stat-value"><?php echo number_format($stats['avg_engagement_days'] ?? 0, 1); ?></div>
                    <div style="font-size: 14px; margin-top: 4px; opacity: 0.9;">jours</div>
                </div>
            </div>
        </div>

        <!-- Liste d'Intervention -->
        <div class='moodleia-section intervention-list'>
            <h3>
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                Liste d'Intervention (Risque > 70%)
            </h3>
            
            <?php if (empty($interventions['students'])): ?>
                <p class='risk-low'>
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Aucun étudiant ne dépasse le seuil d'intervention.
                </p>
            <?php else: ?>
                <p style="margin-bottom: 16px;">
                    <strong>Priorité Élevée:</strong> 
                    <span class="priority-badge priority-high"><?php echo $interventions['high_priority'] ?? 0; ?> étudiants</span>
                </p>
                <table>
                    <thead>
                        <tr>
                            <th>ID Étudiant</th>
                            <th>Probabilité</th>
                            <th>Priorité</th>
                            <th>Actions Recommandées</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($interventions['students'] as $student): 
                            $priority = $student['priority'] ?? 'low';
                            $priority_class = $priority === 'high' ? 'priority-high' : 'priority-medium';
                            $actions = implode(', ', $student['recommended_actions'] ?? []);
                        ?>
                            <tr>
                                <td><a href='#' title='Voir le détail'><?php echo $student['student_id'] ?? 'N/A'; ?></a></td>
                                <td><strong><?php echo $format_proba($student['risk_probability'] ?? 0); ?></strong></td>
                                <td><span class="priority-badge <?php echo $priority_class; ?>"><?php echo $priority; ?></span></td>
                                <td><?php echo $actions; ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>

    <?php else: 
    // --- Rendu du Tableau de Bord ÉTUDIANT ---
    $performance = $data['performance'] ?? [];
    $predictions = $data['predictions'] ?? [];
    $recommendations = $data['recommendations'] ?? [];
    $alerts = $data['alerts'] ?? [];
    $insights = $data['insights'] ?? [];
    
    $risk_data = $predictions['at_risk'] ?? [];
    $is_at_risk = $risk_data['is_at_risk'] ?? false;
    $dropout_data = $predictions['dropout'] ?? [];
    ?>

        <h2>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            Tableau de Bord Adaptatif Étudiant
        </h2>
        <p style="color: #64748b; margin: -16px 0 24px 0;">Bienvenue, Étudiant #<?php echo $user_id; ?>. Voici vos analyses en temps réel.</p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
            
            <!-- SECTION 1: Statut Global et Performances -->
            <div style="grid-column: 1 / -1;">
                <div class='moodleia-section' style="border-left: 4px solid #3b82f6;">
                    <h3>
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                        </svg>
                        Performance et Statut Actuels
                    </h3>
                    
                    <!-- Statut de Risque -->
                    <div style="padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid; <?php echo $is_at_risk ? 'background: #fef2f2; border-color: #dc2626;' : 'background: #f0fdf4; border-color: #059669;'; ?>">
                        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                            <div style="display: flex; align-items: center;">
                                <?php if ($is_at_risk): ?>
                                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 24px; height: 24px; margin-right: 12px; color: #dc2626;">
                                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                                        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                                    </svg>
                                <?php else: ?>
                                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 24px; height: 24px; margin-right: 12px; color: #059669;">
                                        <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                <?php endif; ?>
                                <span style="font-size: 18px; font-weight: 700; <?php echo $is_at_risk ? 'color: #991b1b;' : 'color: #065f46;'; ?>">
                                    Statut de Réussite: <?php echo $is_at_risk ? 'À Risque' : 'Bon Statut'; ?>
                                </span>
                            </div>
                            <span style="font-size: 14px; color: #64748b;">
                                Résultat final prédit: <?php echo ($dropout_data['will_dropout'] ?? false) ? 'Abandon' : 'Poursuite'; ?>
                            </span>
                        </div>
                    </div>

                    <!-- Cards de Performance -->
                    <div class="stats-grid">
                        <div class="stat-card" style="background: linear-gradient(135deg, #9333ea 0%, #7e22ce 100%);">
                            <div class="stat-label">Score Moyen</div>
                            <div class="stat-value"><?php echo number_format($performance['avg_score'] ?? 0, 1); ?>%</div>
                        </div>
                        <div class="stat-card" style="background: linear-gradient(135deg, #059669 0%, #047857 100%);">
                            <div class="stat-label">Évaluations</div>
                            <div class="stat-value"><?php echo $performance['num_assessments'] ?? 'N/A'; ?></div>
                        </div>
                        <div class="stat-card" style="background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);">
                            <div class="stat-label">Jours Actifs</div>
                            <div class="stat-value"><?php echo $performance['active_days'] ?? 'N/A'; ?></div>
                        </div>
                        <div class="stat-card" style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);">
                            <div class="stat-label">Taux Retard</div>
                            <div class="stat-value"><?php echo number_format(($performance['late_submission_rate'] ?? 0) * 100, 0); ?>%</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SECTION 2: Alertes et Insights -->
            <div style="grid-column: 1 / -1;">
                <?php if (!empty($alerts)): ?>
                    <div class='moodleia-section' style="border-left: 4px solid #f59e0b;">
                        <h3>
                            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                            </svg>
                            Alertes et Insights (<?php echo count($alerts); ?>)
                            <span style="color: #64748b; font-weight: 400; font-size: 14px; margin-left: 8px;">
                                - Engagement: <?php echo $insights['engagement_level'] ?? 'N/A'; ?>
                            </span>
                        </h3>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <?php foreach ($alerts as $alert): 
                                $level = $alert['level'] ?? 'low';
                                $alert_bg = $level === 'high' ? '#fef2f2' : ($level === 'medium' ? '#fffbeb' : '#eff6ff');
                                $alert_border = $level === 'high' ? '#dc2626' : ($level === 'medium' ? '#d97706' : '#3b82f6');
                                $alert_color = $level === 'high' ? '#991b1b' : ($level === 'medium' ? '#92400e' : '#1e40af');
                            ?>
                                <div style="display: flex; align-items: flex-start; gap: 12px; padding: 16px; border-radius: 8px; background: <?php echo $alert_bg; ?>; border-left: 4px solid <?php echo $alert_border; ?>;">
                                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink: 0; margin-top: 2px; color: <?php echo $alert_border; ?>;">
                                        <?php if ($level === 'high'): ?>
                                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                                            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                                        <?php else: ?>
                                            <polyline points="20 6 9 17 4 12"/>
                                        <?php endif; ?>
                                    </svg>
                                    <div style="flex: 1;">
                                        <p style="font-weight: 600; font-size: 14px; color: <?php echo $alert_color; ?>; text-transform: capitalize;">
                                            <?php echo str_replace('_', ' ', $alert['type'] ?? 'Alerte'); ?>:
                                        </p>
                                        <p style="font-size: 14px; color: #374151; margin-top: 4px;"><?php echo $alert['message'] ?? 'Message indisponible'; ?></p>
                                        <p style="font-size: 12px; font-style: italic; color: #6b7280; margin-top: 6px;">
                                            Action recommandée: <?php echo $alert['action'] ?? 'Consulter le chatbot.'; ?>
                                        </p>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                <?php endif; ?>
            </div>

            <!-- SECTION 3: Recommandations Personnalisées -->
            <?php if (!empty($recommendations)): ?>
                <div style="grid-column: 1 / -1;">
                    <div class='moodleia-section' style="border-left: 4px solid #059669;">
                        <h3>
                            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                            </svg>
                            Ressources Recommandées
                        </h3>
                        <div style="display: flex; flex-direction: column;">
                            <?php foreach ($recommendations as $index => $rec): 
                                $rec_type = $rec['type'] ?? 'Ressource';
                                $rec_color = $rec_type === 'Video' ? '#dc2626' : ($rec_type === 'Forum' ? '#059669' : '#9333ea');
                            ?>
                                <a href="<?php echo $rec['link'] ?? '#'; ?>" style="display: flex; align-items: center; padding: 12px; text-decoration: none; border-radius: 8px; transition: background-color 0.2s; <?php echo $index > 0 ? 'border-top: 1px solid #f1f5f9;' : ''; ?>" onmouseover="this.style.backgroundColor='#f8fafc'" onmouseout="this.style.backgroundColor='transparent'">
                                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: <?php echo $rec_color; ?>; margin-right: 12px; flex-shrink: 0;">
                                        <?php if ($rec_type === 'Video'): ?>
                                            <polygon points="5 3 19 12 5 21 5 3"/>
                                        <?php elseif ($rec_type === 'Forum'): ?>
                                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                                            <circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                                            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                        <?php elseif ($rec_type === 'Quiz'): ?>
                                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                                        <?php else: ?>
                                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                        <?php endif; ?>
                                    </svg>
                                    <div style="flex: 1;">
                                        <p style="font-size: 14px; font-weight: 500; color: #374151;"><?php echo $rec['title'] ?? $rec['resource_name'] ?? 'Nom inconnu'; ?></p>
                                        <p style="font-size: 12px; color: #9ca3af; margin-top: 2px;">
                                            <?php echo $rec_type; ?>
                                            <?php if (isset($rec['score'])): ?>
                                                <span style="color: #64748b;"> - Score: <?php echo $rec['score']; ?></span>
                                            <?php endif; ?>
                                        </p>
                                    </div>
                                </a>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
            <?php endif; ?>

        </div>

        <!-- SECTION 4: Chatbot MoodleIA -->
        <div style="grid-column: 1 / -1;">
            <div class='moodleia-section' style="border-left: 4px solid #3b82f6; padding: 0; overflow: hidden;">
                <!-- En-tête du Chatbot -->
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 20px; display: flex; align-items: center;">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 24px; height: 24px; margin-right: 12px;">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    <h3 style="color: white; margin: 0;">Chatbot MoodleIA - Assistant IA Personnel</h3>
                </div>

                <!-- Zone de Chat -->
                <div id="moodleia-chat-messages" style="height: 400px; overflow-y: auto; padding: 20px; background: #f8fafc;">
                    <!-- Message initial du bot -->
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 16px;">
                        <div style="background: #3b82f6; color: white; padding: 12px 16px; border-radius: 16px; border-top-left-radius: 4px; max-width: 70%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                                <svg style="width: 16px; height: 16px; margin-right: 6px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                <strong style="font-size: 12px;">MoodleIA</strong>
                            </div>
                            <p style="margin: 0; font-size: 14px; line-height: 1.5;">
                                Bonjour ! Je suis MoodleIA, votre assistant d'apprentissage adaptatif. 
                                Je peux répondre à vos questions sur vos cours, vos performances, ou vous aider à trouver des ressources. 
                                Posez-moi une question ! (Ex: "Comment améliorer ma note moyenne?")
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Formulaire d'Entrée -->
                <form id="moodleia-chat-form" style="padding: 16px; background: white; border-top: 1px solid #e5e7eb;">
                    <div style="display: flex; gap: 12px;">
                        <input 
                            type="text" 
                            id="moodleia-chat-input" 
                            placeholder="Posez votre question à MoodleIA..." 
                            style="flex: 1; padding: 12px; border: 1px solid #d1d5db; border-radius: 12px; font-size: 14px; transition: all 0.2s;"
                            onfocus="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 0 0 3px rgba(59, 130, 246, 0.1)';"
                            onblur="this.style.borderColor='#d1d5db'; this.style.boxShadow='none';"
                        />
                        <button 
                            type="submit" 
                            id="moodleia-chat-submit"
                            style="padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px;"
                            onmouseover="this.style.background='#2563eb';"
                            onmouseout="this.style.background='#3b82f6';"
                        >
                            <span id="moodleia-submit-text">Envoyer</span>
                            <svg id="moodleia-submit-icon" style="width: 16px; height: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                            </svg>
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <script>
        (function() {
            const API_BASE_URL = 'http://localhost:5000';
            const STUDENT_ID = <?php echo $user_id; ?>;
            
            const chatForm = document.getElementById('moodleia-chat-form');
            const chatInput = document.getElementById('moodleia-chat-input');
            const chatMessages = document.getElementById('moodleia-chat-messages');
            const submitButton = document.getElementById('moodleia-chat-submit');
            const submitText = document.getElementById('moodleia-submit-text');
            const submitIcon = document.getElementById('moodleia-submit-icon');
            
            let isLoading = false;
            
            // Fonction pour scroller en bas
            function scrollToBottom() {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // Fonction pour ajouter un message utilisateur
            function addUserMessage(message) {
                const messageDiv = document.createElement('div');
                messageDiv.style.cssText = 'display: flex; justify-content: flex-end; margin-bottom: 16px;';
                messageDiv.innerHTML = `
                    <div style="background: #e5e7eb; color: #1f2937; padding: 12px 16px; border-radius: 16px; border-top-right-radius: 4px; max-width: 70%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <p style="margin: 0; font-size: 14px; line-height: 1.5;">${escapeHtml(message)}</p>
                    </div>
                `;
                chatMessages.appendChild(messageDiv);
                scrollToBottom();
            }
            
            // Fonction pour ajouter un message bot
            function addBotMessage(message) {
                const messageDiv = document.createElement('div');
                messageDiv.style.cssText = 'display: flex; justify-content: flex-start; margin-bottom: 16px;';
                messageDiv.innerHTML = `
                    <div style="background: #3b82f6; color: white; padding: 12px 16px; border-radius: 16px; border-top-left-radius: 4px; max-width: 70%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; margin-bottom: 6px;">
                            <svg style="width: 16px; height: 16px; margin-right: 6px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                            </svg>
                            <strong style="font-size: 12px;">MoodleIA</strong>
                        </div>
                        <p style="margin: 0; font-size: 14px; line-height: 1.5;">${escapeHtml(message)}</p>
                    </div>
                `;
                chatMessages.appendChild(messageDiv);
                scrollToBottom();
            }
            
            // Fonction pour afficher le chargement
            function showLoading() {
                const loadingDiv = document.createElement('div');
                loadingDiv.id = 'moodleia-loading';
                loadingDiv.style.cssText = 'display: flex; justify-content: flex-start; margin-bottom: 16px;';
                loadingDiv.innerHTML = `
                    <div style="background: #eff6ff; color: #1e40af; padding: 12px 16px; border-radius: 16px; border-top-left-radius: 4px; max-width: 70%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); animation: pulse 1.5s infinite;">
                        <p style="margin: 0; font-size: 14px;">MoodleIA est en train d'écrire...</p>
                    </div>
                `;
                chatMessages.appendChild(loadingDiv);
                scrollToBottom();
            }
            
            // Fonction pour supprimer le chargement
            function hideLoading() {
                const loadingDiv = document.getElementById('moodleia-loading');
                if (loadingDiv) {
                    loadingDiv.remove();
                }
            }
            
            // Fonction pour échapper le HTML
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            // Fonction pour désactiver/activer le formulaire
            function setFormState(disabled) {
                isLoading = disabled;
                chatInput.disabled = disabled;
                submitButton.disabled = disabled;
                submitButton.style.opacity = disabled ? '0.6' : '1';
                submitButton.style.cursor = disabled ? 'not-allowed' : 'pointer';
                
                if (disabled) {
                    submitText.textContent = 'Envoi...';
                    submitIcon.innerHTML = '<circle cx="12" cy="12" r="10" style="animation: spin 1s linear infinite;"/>';
                } else {
                    submitText.textContent = 'Envoyer';
                    submitIcon.innerHTML = '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>';
                }
            }
            
            // Gestionnaire de soumission du formulaire
            chatForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const message = chatInput.value.trim();
                if (!message || isLoading) return;
                
                // Ajouter le message utilisateur
                addUserMessage(message);
                chatInput.value = '';
                
                // Désactiver le formulaire et afficher le chargement
                setFormState(true);
                showLoading();
                
                try {
                    const response = await fetch(`${API_BASE_URL}/api/chatbot/chat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            student_id: STUDENT_ID,
                            message: message
                        })
                    });
                    
                    hideLoading();
                    
                    if (!response.ok) {
                        throw new Error(`Erreur API: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    addBotMessage(data.bot_response);
                    
                } catch (error) {
                    console.error('Erreur du chatbot:', error);
                    hideLoading();
                    addBotMessage(
                        "Désolé, une erreur de connexion est survenue. Le chatbot n'est pas disponible pour le moment. " +
                        "Veuillez vérifier que l'API Flask est bien démarrée (http://localhost:5000)."
                    );
                } finally {
                    setFormState(false);
                    chatInput.focus();
                }
            });
            
            // Animation de pulse pour le chargement
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
            
            // Focus automatique sur l'input au chargement
            chatInput.focus();
        })();
        </script>

    <?php endif; ?>

</div>