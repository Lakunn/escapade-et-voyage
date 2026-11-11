<?php
/**
 * Bloc newsletter : affiché uniquement si newsletter.action est renseigné dans config/site.yml.
 */
$vr_action = vr_config( 'newsletter.action' );
if ( ! $vr_action ) {
	return;
}
?>
<section class="newsletter" aria-labelledby="nl-title">
	<div>
		<h2 id="nl-title"><?php echo esc_html( vr_config( 'newsletter.title', 'La veille SEO & GEO' ) ); ?></h2>
		<p><?php echo esc_html( vr_config( 'newsletter.text', '' ) ); ?></p>
	</div>
	<form action="<?php echo esc_url( $vr_action ); ?>" method="post" target="_blank">
		<label class="screen-reader-text" for="nl-email">Adresse e-mail</label>
		<input id="nl-email" type="email" name="<?php echo esc_attr( vr_config( 'newsletter.field', 'EMAIL' ) ); ?>" placeholder="ton@email.fr" required>
		<button class="btn" type="submit"><?php echo esc_html( vr_config( 'newsletter.button', "S'inscrire" ) ); ?></button>
	</form>
</section>
