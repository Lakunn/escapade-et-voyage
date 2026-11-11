<?php
$vr_photo = vr_config( 'author.photo' );
?>
<aside class="author-box" aria-label="À propos de l'auteur">
	<?php if ( $vr_photo ) : ?>
		<img src="<?php echo esc_url( $vr_photo ); ?>" alt="<?php echo esc_attr( vr_config( 'author.name' ) ); ?>" width="84" height="84" loading="lazy">
	<?php else : ?>
		<span class="author-initial" aria-hidden="true"><?php echo esc_html( vr_initial( vr_config( 'brand.name', 'G' ) ) ); ?></span>
	<?php endif; ?>
	<div>
		<p class="name"><a href="<?php echo esc_url( home_url( (string) vr_config( 'author.page', '/' ) ) ); ?>"><?php echo esc_html( vr_config( 'author.name', get_the_author() ) ); ?></a></p>
		<p class="role"><?php echo esc_html( vr_config( 'author.role', '' ) ); ?></p>
		<p><?php echo esc_html( vr_config( 'author.bio', '' ) ); ?></p>
		<p class="links">
			<?php foreach ( (array) vr_config( 'author.links', array() ) as $vr_link ) : ?>
				<a href="<?php echo esc_url( $vr_link['url'] ); ?>" rel="me noopener" target="_blank"><?php echo esc_html( $vr_link['label'] ); ?></a>
			<?php endforeach; ?>
		</p>
	</div>
</aside>
