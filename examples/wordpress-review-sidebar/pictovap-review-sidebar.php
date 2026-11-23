<?php
/**
 * Plugin Name: Pictovap Gutenberg Review (Reference)
 * Description: Offline Decision Pack review draft inside Gutenberg. Does not publish or change post metadata.
 * Version: 0.1.0
 * Requires at least: 6.6
 * Requires PHP: 7.4
 * License: MIT
 */

defined( 'ABSPATH' ) || exit;

/**
 * Only editors who can modify the specific existing post see the sidebar.
 * No REST route, post meta, media upload or save hook is registered.
 */
function pictovap_review_enqueue_sidebar() {
    $screen = get_current_screen();
    if ( ! $screen || 'post' !== $screen->base ) {
        return;
    }

    // Existing posts only. The WordPress-post plan must match this post ID.
    $post_id = isset( $_GET['post'] ) ? absint( wp_unslash( $_GET['post'] ) ) : 0;
    if ( ! $post_id || ! get_post( $post_id ) || ! current_user_can( 'edit_post', $post_id ) ) {
        return;
    }

    $root = plugin_dir_url( __FILE__ );
    wp_enqueue_script(
        'pictovap-review-model',
        $root . 'assets/review-model.js',
        array(),
        '0.1.0',
        true
    );
    wp_enqueue_script(
        'pictovap-local-preview',
        $root . 'assets/local-preview.js',
        array(),
        '0.1.0',
        true
    );
    wp_enqueue_script(
        'pictovap-review-sidebar',
        $root . 'assets/sidebar.js',
        array( 'pictovap-review-model', 'pictovap-local-preview', 'wp-plugins', 'wp-editor', 'wp-element', 'wp-components' ),
        '0.1.0',
        true
    );
    wp_localize_script(
        'pictovap-review-sidebar',
        'PictovapReviewConfig',
        array(
            'postId' => $post_id,
            // Display identity only; exported claims remain untrusted until Core validation.
            'actor'  => wp_get_current_user()->user_login,
        )
    );
    wp_enqueue_style(
        'pictovap-review-sidebar',
        $root . 'assets/sidebar.css',
        array(),
        '0.1.0'
    );
}
add_action( 'enqueue_block_editor_assets', 'pictovap_review_enqueue_sidebar' );
