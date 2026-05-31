<?php
$id = 264443;
$post = get_post($id);
$content = $post ? $post->post_content : '';
$counts = ['core_image'=>0, 'image_missing_id'=>0, 'free_html'=>0];
function walk_verify($blocks, &$counts) {
    foreach ($blocks as $block) {
        $name = $block['blockName'] ?? null;
        if ($name === 'core/image') {
            $counts['core_image']++;
            if (!isset($block['attrs']['id'])) $counts['image_missing_id']++;
        }
        if ($name === null && trim($block['innerHTML'] ?? '') !== '') $counts['free_html']++;
        if (!empty($block['innerBlocks'])) walk_verify($block['innerBlocks'], $counts);
    }
}
$blocks = parse_blocks($content);
walk_verify($blocks, $counts);
preg_match_all('/<!-- wp:image\b/i', $content, $rawImages);
preg_match_all('/wp-image-([0-9]+)/', $content, $imageIds);
echo wp_json_encode([
    'post_id'=>$id,
    'raw_image_comments'=>count($rawImages[0]),
    'wp_image_ids'=>array_values(array_unique($imageIds[1])),
    'top_blocks'=>count($blocks),
] + $counts, JSON_UNESCAPED_UNICODE) . "\n";
