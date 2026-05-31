<?php
$ids = [264462,264463,264486,264459,264458,264585,249223,264454,264532,264525,264528,152168,260971];
function count_blocks_deep($blocks, &$counts) {
    foreach ($blocks as $block) {
        $name = $block['blockName'] ?? null;
        if ($name === 'core/image') {
            $counts['core_image']++;
            if (!isset($block['attrs']['id'])) $counts['image_missing_id']++;
        }
        if ($name === null && trim($block['innerHTML'] ?? '') !== '') {
            $counts['free_html']++;
        }
        if (!empty($block['innerBlocks'])) count_blocks_deep($block['innerBlocks'], $counts);
    }
}
foreach ($ids as $id) {
    $post = get_post($id);
    $content = $post ? $post->post_content : '';
    $counts = ['core_image'=>0, 'image_missing_id'=>0, 'free_html'=>0];
    $blocks = parse_blocks($content);
    count_blocks_deep($blocks, $counts);
    preg_match_all('/<!-- wp:image\b/i', $content, $rawImages);
    preg_match_all('/wp-image-([0-9]+)/', $content, $imageIds);
    echo wp_json_encode([
        'post_id'=>$id,
        'top_blocks'=>count($blocks),
        'raw_image_comments'=>count($rawImages[0]),
        'wp_image_ids'=>count(array_unique($imageIds[1])),
    ] + $counts, JSON_UNESCAPED_UNICODE) . "\n";
}
