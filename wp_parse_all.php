<?php
$id = 264462;
$post = get_post($id);
$blocks = parse_blocks($post->post_content);
foreach ($blocks as $i => $block) {
    $name = $block['blockName'] ?? 'NULL';
    $inner = $block['innerHTML'] ?? '';
    if (strpos($inner, 'wp-image') !== false || $name === 'core/image' || $name === null) {
        echo wp_json_encode(['i'=>$i,'name'=>$name,'attrs'=>$block['attrs'] ?? [], 'inner'=>preg_replace('/\s+/', ' ', substr($inner,0,500))], JSON_UNESCAPED_UNICODE) . "\n";
    }
}
