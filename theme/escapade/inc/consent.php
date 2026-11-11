<?php
/**
 * Consentement aux cookies de mesure d'audience (Google Analytics via Site Kit).
 *
 * - Google Consent Mode v2 : tout est refusé par défaut, AVANT le chargement de gtag par Site Kit.
 *   Aucun cookie Analytics n'est déposé tant que le visiteur n'a pas accepté.
 * - Bandeau avec « Accepter » et « Refuser » au même niveau (exigence CNIL), choix mémorisé 6 mois.
 * - Lien « Gérer les cookies » dans le pied de page pour revenir sur son choix.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! vr_config( 'analytics' ) ) {
	return; // Aucun outil de mesure déclaré dans config/site.yml : pas de bandeau.
}

// Doit passer avant Site Kit : priorité 0.
add_action(
	'wp_head',
	function () {
		?>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent', 'default', {analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', wait_for_update: 500});
(function () {
  try {
    var m = document.cookie.match(/(?:^|; )vr_consent=(granted|denied)/);
    if (m && m[1] === 'granted') { gtag('consent', 'update', {analytics_storage: 'granted'}); }
  } catch (e) {}
})();
</script>
		<?php
	},
	0
);

add_action(
	'wp_footer',
	function () {
		?>
<div class="consent" id="vr-consent" role="dialog" aria-live="polite" aria-label="Cookies de mesure d'audience" hidden>
	<p>Ce site utilise Google Analytics pour mesurer son audience, uniquement avec votre accord. <a href="<?php echo esc_url( home_url( '/politique-de-confidentialite/' ) ); ?>">En savoir plus</a></p>
	<div class="consent-actions">
		<button type="button" class="btn consent-btn" data-consent="denied">Refuser</button>
		<button type="button" class="btn consent-btn" data-consent="granted">Accepter</button>
	</div>
</div>
		<?php
	},
	5
);
