<form class="search-form" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
	<label class="screen-reader-text" for="sf-<?php echo esc_attr( wp_unique_id() ); ?>">Rechercher</label>
	<input type="search" name="s" placeholder="GEO, indexation, netlinking…" value="<?php echo esc_attr( get_search_query() ); ?>">
	<button class="btn" type="submit">Rechercher</button>
</form>
