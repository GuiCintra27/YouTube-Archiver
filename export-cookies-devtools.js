/**
 * Script para exportar cookies do YouTube no formato Netscape
 *
 * INSTRUÇÕES:
 * 1. Abra https://www.youtube.com (logado na sua conta)
 * 2. Pressione F12 (DevTools)
 * 3. Vá na aba Console
 * 4. Cole TODO este script e pressione Enter
 * 5. Cookies serão copiados automaticamente
 * 6. Cole no arquivo python/cookies.txt
 */

(function() {
    console.clear();
    console.log('🍪 Exportando cookies do YouTube...\n');

    // Pegar todos os cookies
    const cookies = document.cookie.split(';').map(c => c.trim());

    // Cookies importantes do YouTube
    const importantCookies = [
        'CONSENT',
        'VISITOR_INFO1_LIVE',
        'LOGIN_INFO',
        'PREF',
        'SID',
        'SSID',
        'APISID',
        'SAPISID',
        'HSID',
        '__Secure-1PSID',
        '__Secure-3PSID'
    ];

    // Função para pegar cookie storage (mais completo)
    function getAllCookies() {
        return document.cookie.split(';').reduce((cookies, cookie) => {
            const [name, value] = cookie.split('=').map(c => c.trim());
            cookies[name] = value;
            return cookies;
        }, {});
    }

    const allCookies = getAllCookies();

    // Gerar arquivo no formato Netscape
    const netscapeCookies = [];
    netscapeCookies.push('# Netscape HTTP Cookie File');
    netscapeCookies.push('# This file was generated using DevTools');
    netscapeCookies.push('# Generated: ' + new Date().toISOString());
    netscapeCookies.push('');

    // Expiry: 1 ano a partir de agora
    const expiry = Math.floor(Date.now() / 1000) + 31536000;

    let foundCount = 0;

    for (const [name, value] of Object.entries(allCookies)) {
        if (value && value !== 'undefined') {
            // Determinar se é secure
            const isSecure = name.startsWith('__Secure') || name.includes('SID');
            const secure = isSecure ? 'TRUE' : 'FALSE';

            // Formato Netscape:
            // domain flag path secure expiry name value
            netscapeCookies.push(
                `.youtube.com\tTRUE\t/\t${secure}\t${expiry}\t${name}\t${value}`
            );

            if (importantCookies.includes(name)) {
                foundCount++;
                console.log(`✅ ${name} (${value.substring(0, 20)}...)`);
            }
        }
    }

    const result = netscapeCookies.join('\n');

    // Copiar para clipboard
    const textarea = document.createElement('textarea');
    textarea.value = result;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    console.log('\n' + '='.repeat(50));
    console.log('📊 Estatísticas:');
    console.log(`   Total de cookies: ${Object.keys(allCookies).length}`);
    console.log(`   Cookies importantes: ${foundCount}/${importantCookies.length}`);
    console.log('='.repeat(50));
    console.log('\n✅ COOKIES COPIADOS PARA CLIPBOARD!\n');
    console.log('📝 Próximos passos:');
    console.log('   1. Abra o arquivo: python/cookies.txt');
    console.log('   2. Delete todo o conteúdo');
    console.log('   3. Cole (Ctrl+V) os cookies copiados');
    console.log('   4. Salve o arquivo');
    console.log('   5. Teste: cd python && source .venv/bin/activate');
    console.log('   6. python main.py download "URL" --cookies-file cookies.txt');
    console.log('\n' + '='.repeat(50));

    // Avisos
    if (foundCount < 5) {
        console.warn('\n⚠️  ATENÇÃO: Poucos cookies importantes encontrados!');
        console.warn('   Certifique-se de estar LOGADO no YouTube');
        console.warn('   Navegue um pouco antes de exportar');
    }

    // Retornar para inspeção
    return {
        cookies: allCookies,
        netscapeFormat: result,
        importantFound: foundCount,
        total: Object.keys(allCookies).length
    };
})();
