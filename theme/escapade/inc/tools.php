<?php
/**
 * Outils voyage : [ev_budget], [ev_depenses], [ev_decalage], [ev_bagages], [ev_trajet].
 * Chaque shortcode affiche un formulaire accessible ; le calcul est fait par assets/tools.js
 * (chargé uniquement sur les pages qui utilisent un outil). Sans JavaScript, un message l'indique.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function gc_tools_enqueue() {
	wp_enqueue_script( 'gc-tools', get_template_directory_uri() . '/assets/tools.js', array(), (string) filemtime( get_template_directory() . '/assets/tools.js' ), array( 'strategy' => 'defer', 'in_footer' => true ) );
}

function gc_tool_wrap( $id, $title, $inner ) {
	gc_tools_enqueue();
	return sprintf(
		'<div class="gc-tool" data-tool="%1$s" id="outil-%1$s"><p class="gc-tool-title">%2$s</p><form class="gc-tool-form" novalidate>%3$s</form><div class="gc-tool-result" aria-live="polite"></div><noscript><p>Cet outil nécessite JavaScript.</p></noscript></div>',
		esc_attr( $id ),
		esc_html( $title ),
		$inner
	);
}

function gc_field( $name, $label, $control, $help = '' ) {
	$id = 'gc-' . $name . '-' . wp_unique_id();
	return sprintf(
		'<div class="gc-field"><label for="%1$s">%2$s</label>%3$s%4$s</div>',
		esc_attr( $id ),
		esc_html( $label ),
		str_replace( '{id}', esc_attr( $id ), $control ),
		$help ? '<small>' . esc_html( $help ) . '</small>' : ''
	);
}

function gc_select( $name, array $options ) {
	$html = '<select id="{id}" name="' . esc_attr( $name ) . '">';
	foreach ( $options as $value => $label ) {
		$html .= '<option value="' . esc_attr( $value ) . '">' . esc_html( $label ) . '</option>';
	}
	return $html . '</select>';
}

function gc_number( $name, $attrs = '' ) {
	return '<input id="{id}" type="number" inputmode="decimal" name="' . esc_attr( $name ) . '" ' . $attrs . '>';
}

function gc_text( $name, $attrs = '' ) {
	return '<input id="{id}" type="text" name="' . esc_attr( $name ) . '" ' . $attrs . '>';
}

/* Budget de voyage ------------------------------------------------------- */
add_shortcode(
	'ev_budget',
	function () {
		$f  = '<div class="gc-grid">';
		$f .= gc_field( 'jours', 'Durée du voyage (jours)', gc_number( 'jours', 'min="1" max="365" step="1" placeholder="ex. 10"' ) );
		$f .= gc_field( 'voyageurs', 'Nombre de voyageurs', gc_number( 'voyageurs', 'min="1" max="30" step="1" placeholder="ex. 2"' ) );
		$f .= '</div><p class="gc-hint">Montants en euros pour tout le groupe. Laissez vide ce qui ne vous concerne pas.</p><div class="gc-grid">';
		$rows = array(
			'transport' => array( 'Billets aller-retour (avion, train…)', 'once' ),
			'assurance' => array( 'Assurance, visa, vaccins', 'once' ),
			'logement'  => array( 'Hébergement (par nuit)', 'night' ),
			'repas'     => array( 'Repas et boissons (par jour)', 'day' ),
			'local'     => array( 'Transports sur place (par jour)', 'day' ),
			'activites' => array( 'Visites et activités (total)', 'once' ),
			'divers'    => array( 'Souvenirs, imprévus (total)', 'once' ),
		);
		foreach ( $rows as $key => $row ) {
			$f .= gc_field( $key, $row[0], gc_number( $key, 'min="0" step="1" data-period="' . esc_attr( $row[1] ) . '" placeholder="0"' ) );
		}
		$f .= '</div>' . gc_field( 'marge', 'Marge de sécurité', gc_select( 'marge', array( '10' => '10 % (conseillé)', '0' => 'Aucune', '5' => '5 %', '15' => '15 %', '20' => '20 % (pays à prix variables)' ) ) );
		$f .= '<button class="btn" type="submit">Calculer le budget</button>';
		return gc_tool_wrap( 'budget', 'Budget de voyage : total, par personne et par jour', $f );
	}
);

/* Partage des dépenses ---------------------------------------------------- */
add_shortcode(
	'ev_depenses',
	function () {
		$f  = gc_field( 'lignes', 'Dépenses (une par ligne : qui a payé ; montant ; pour qui)', '<textarea id="{id}" name="lignes" rows="7" placeholder="' . esc_attr( "Léa ; 240 ; tous\nKarim ; 86,50 ; tous\nLéa ; 30 ; Léa, Karim\nSam ; 120 ; tous" ) . '"></textarea>', 'Laissez « tous » pour partager à parts égales entre tous les participants, ou listez les prénoms concernés.' );
		$f .= '<button class="btn" type="submit">Qui doit combien à qui ?</button>';
		return gc_tool_wrap( 'depenses', 'Partage des dépenses entre voyageurs', $f );
	}
);

/* Décalage horaire -------------------------------------------------------- */
add_shortcode(
	'ev_decalage',
	function () {
		$zones = array(
			'Europe/Paris' => 'Paris', 'Europe/London' => 'Londres, Lisbonne (Europe/London)', 'Atlantic/Reykjavik' => 'Reykjavik',
			'Europe/Athens' => 'Athènes, Helsinki', 'Europe/Istanbul' => 'Istanbul', 'Africa/Casablanca' => 'Marrakech, Casablanca',
			'Africa/Cairo' => 'Le Caire', 'Africa/Johannesburg' => 'Le Cap, Johannesburg', 'Africa/Nairobi' => 'Nairobi, Zanzibar',
			'Asia/Dubai' => 'Dubaï, Oman', 'Indian/Mauritius' => 'Maurice', 'Indian/Reunion' => 'La Réunion', 'Asia/Kolkata' => 'Inde',
			'Asia/Colombo' => 'Sri Lanka', 'Asia/Kathmandu' => 'Népal', 'Asia/Bangkok' => 'Bangkok, Vietnam, Cambodge, Laos',
			'Asia/Makassar' => 'Bali', 'Asia/Singapore' => 'Singapour, Kuala Lumpur', 'Asia/Shanghai' => 'Chine', 'Asia/Seoul' => 'Séoul',
			'Asia/Tokyo' => 'Tokyo', 'Australia/Sydney' => 'Sydney, Melbourne', 'Pacific/Auckland' => 'Nouvelle-Zélande', 'Pacific/Tahiti' => 'Tahiti',
			'America/Martinique' => 'Martinique, Guadeloupe', 'America/Montreal' => 'Montréal, Québec', 'America/New_York' => 'New York, Miami',
			'America/Chicago' => 'Chicago', 'America/Denver' => 'Denver', 'America/Los_Angeles' => 'Los Angeles, San Francisco',
			'America/Mexico_City' => 'Mexico', 'America/Cancun' => 'Cancún, Yucatán', 'America/Havana' => 'Cuba', 'America/Costa_Rica' => 'Costa Rica',
			'America/Lima' => 'Pérou', 'America/Bogota' => 'Colombie', 'America/Sao_Paulo' => 'Brésil (Rio, São Paulo)',
			'America/Argentina/Buenos_Aires' => 'Argentine', 'America/Santiago' => 'Chili',
		);
		$f  = '<div class="gc-grid">' . gc_field( 'depart', 'Départ', gc_select( 'depart', $zones ) );
		$dest = $zones;
		$f .= gc_field( 'dest', 'Destination', str_replace( 'value="Asia/Tokyo"', 'value="Asia/Tokyo" selected', gc_select( 'dest', $dest ) ) );
		$f .= gc_field( 'date', 'Date du départ', '<input id="{id}" type="date" name="date">' ) . '</div>';
		$f .= '<button class="btn" type="submit">Calculer le décalage</button>';
		return gc_tool_wrap( 'decalage', 'Décalage horaire et récupération du jet lag', $f );
	}
);

/* Liste de bagages -------------------------------------------------------- */
add_shortcode(
	'ev_bagages',
	function () {
		$f  = '<div class="gc-grid">' . gc_field( 'jours', 'Durée (jours)', gc_number( 'jours', 'min="1" max="120" step="1" placeholder="ex. 7"' ) );
		$f .= gc_field( 'climat', 'Climat', gc_select( 'climat', array( 'tempere' => 'Tempéré', 'chaud' => 'Chaud', 'tropical' => 'Tropical et humide', 'froid' => 'Froid ou montagne' ) ) );
		$f .= gc_field( 'style', 'Façon de voyager', gc_select( 'style', array( 'mixte' => 'Un peu de tout', 'ville' => 'Villes et culture', 'nature' => 'Randonnée et nature', 'plage' => 'Plage et farniente', 'route' => 'Road trip' ) ) );
		$f .= gc_field( 'sac', 'Bagage', gc_select( 'sac', array( 'cabine' => 'Bagage cabine seul', 'soute' => 'Valise en soute', 'dos' => 'Sac à dos' ) ) ) . '</div>';
		$f .= '<fieldset class="gc-checks"><legend>Options</legend><label><input type="checkbox" name="hors_ue" value="1"> Hors Union européenne</label><label><input type="checkbox" name="enfants" value="1"> Avec des enfants</label><label><input type="checkbox" name="travail" value="1"> Je dois travailler</label></fieldset>';
		$f .= '<button class="btn" type="submit">Générer ma liste</button>';
		return gc_tool_wrap( 'bagages', 'Liste de bagages personnalisée', $f );
	}
);

/* Coût d'un trajet en voiture -------------------------------------------- */
add_shortcode(
	'ev_trajet',
	function () {
		$f  = '<div class="gc-grid">' . gc_field( 'km', 'Distance aller (km)', gc_number( 'km', 'min="1" max="10000" step="1" placeholder="ex. 780"' ) );
		$f .= gc_field( 'ar', 'Trajet', gc_select( 'ar', array( '2' => 'Aller-retour', '1' => 'Aller simple' ) ) );
		$f .= gc_field( 'conso', 'Consommation (L ou kWh aux 100 km)', gc_number( 'conso', 'min="0" max="40" step="0.1" placeholder="ex. 6,5"' ) );
		$f .= gc_field( 'prix', 'Prix du litre ou du kWh (€)', gc_number( 'prix', 'min="0" max="5" step="0.01" placeholder="ex. 1,80"' ), 'Relevez le prix du jour sur prix-carburants.gouv.fr.' );
		$f .= gc_field( 'peages', 'Péages pour un aller (€)', gc_number( 'peages', 'min="0" step="0.1" placeholder="ex. 62"' ), 'Le simulateur de votre société d\'autoroute donne le montant exact.' );
		$f .= gc_field( 'personnes', 'Personnes à bord', gc_number( 'personnes', 'min="1" max="9" step="1" placeholder="ex. 3"' ) );
		$f .= gc_field( 'train', 'Prix d\'un billet de train ou d\'avion équivalent (€, facultatif)', gc_number( 'train', 'min="0" step="1" placeholder="ex. 79"' ), 'Prix par personne pour le même trajet, pour comparer.' ) . '</div>';
		$f .= '<button class="btn" type="submit">Calculer le coût</button>';
		return gc_tool_wrap( 'trajet', 'Coût d\'un trajet en voiture, et comparaison avec le train', $f );
	}
);
