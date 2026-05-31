<?php
$ids = [264462,264463,264486,264459,264458,264585,249223,264454,264532,264525,264528,152168];
function walk_blocks($blocks, &$counts) {
    foreach ($blocks as $block) {
        $name = $block['blockName'] ?? null;
        if ($name === 'core/image') {
            $counts['core_image']++;
            if (!isset($block['attrs']['id'])) {
                $counts['image_missing_id']++;
            }
        } elseif ($name === null && trim($block['innerHTML'] ?? '') !== '') {
            $counts['free_html']++;
        }
        if (!empty($block['innerBlocks'])) {
            walk_blocks($block['innerBlocks'], $counts);
        }
    }
}
foreach ($ids as $id) {
    $post = get_post($id);
    $counts = ['core_image' => 0, 'image_missing_id' => 0, 'free_html' => 0];
    $blocks = parse_blocks($post ? $post->post_content : '');
    walk_blocks($blocks, $counts);
    echo wp_json_encode(['post_id' => $id, 'blocks' => count($blocks)] + $counts, JSON_UNESCAPED_UNICODE) . "\n";
}
