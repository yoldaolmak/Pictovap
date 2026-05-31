<?php
$ids = [264462,260971];
foreach ($ids as $id) {
    $post = get_post($id);
    echo "POST $id\n";
    $blocks = parse_blocks($post ? $post->post_content : '');
    foreach ($blocks as $i => $block) {
        $name = $block['blockName'] ?? 'NULL';
        $attrs = $block['attrs'] ?? [];
        if ($name === 'core/image' || $name === null) {
            $inner = preg_replace('/\s+/', ' ', substr($block['innerHTML'] ?? '', 0, 220));
            echo wp_json_encode(['i'=>$i,'name'=>$name,'attrs'=>$attrs,'inner'=>$inner], JSON_UNESCAPED_UNICODE) . "\n";
        }
    }
}
