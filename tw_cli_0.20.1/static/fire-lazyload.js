/********************************************************************************

	SYNCER 〜 知識、感動をみんなと同期(Sync)するブログ

	* 配布場所
	https://syncer.jp/how-to-setting-lazy-load-images

	* 最終更新日時
	2015/08/15 13:50

	* 作者
	あらゆ

	** 連絡先
	Twitter: https://twitter.com/arayutw
	Facebook: https://www.facebook.com/arayutw
	Google+: https://plus.google.com/114918692417332410369/
	E-mail: info@syncer.jp

	※ バグ、不具合の報告、提案、ご要望など、お待ちしております。
	※ 申し訳ありませんが、ご利用者様、個々の環境における問題はサポートしていません。

********************************************************************************/


/**************************************************

	レイジーロードの起動

**************************************************/

$(function()
{
	$( 'img.lazy' ).lazyload( {
		threshold : 1 ,
		effect : 'fadeIn' ,
		effect_speed: 3000 ,
		failure_limit: 1 ,
	} ) ;
} ) ;