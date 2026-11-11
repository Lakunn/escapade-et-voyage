<?php
$vr_links = paginate_links(
	array(
		'type'      => 'array',
		'prev_text' => '←<span class="screen-reader-text"> Page précédente</span>',
		'next_text' => '<span class="screen-reader-text">Page suivante </span>→',
		'mid_size'  => 1,
	)
);
if ( $vr_links ) {
	echo '<nav class="pagination" aria-label="Pagination">' . implode( '', $vr_links ) . '</nav>'; // phpcs:ignore
}
