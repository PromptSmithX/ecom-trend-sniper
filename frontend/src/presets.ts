// Các bộ subreddit theo từng mảng. Chọn preset sẽ THAY THẾ danh sách hiện tại.

// Chỉ dùng sub theo THỂ LOẠI / LĨNH VỰC (bao quát nhiều chủ đề), không dùng sub fandom 1 người/1 tác phẩm.
export const TREND_POD_US = [
  // Tổng hợp & văn hóa đại chúng
  'popular', 'OutOfTheLoop', 'memes', 'popculturechat', 'entertainment', 'Fauxmoi',
  // Thể thao
  'soccer', 'nfl', 'nba', 'CFB', 'baseball', 'hockey', 'formula1', 'SquaredCircle', 'MMA',
  // Phim, TV, game, anime
  'movies', 'television', 'gaming', 'anime',
  // Thể loại nhạc
  'Music', 'popheads', 'hiphopheads', 'CountryMusic',
];

export interface SubredditPreset {
  id: string;
  label: string;
  title: string;
  subs: string[];
}

export const SUBREDDIT_PRESETS: SubredditPreset[] = [
  {
    id: 'trend_pod_us',
    label: 'Trend POD Mỹ',
    title: 'Mặc định — trend đại chúng tại Mỹ: sự kiện, thể thao, phim, nhạc, game, meme',
    subs: TREND_POD_US,
  },
  {
    id: 'niche_pod_us',
    label: 'Ngách POD Mỹ',
    title: 'Cộng đồng ngách mua POD quanh năm: thú cưng, nghề nghiệp, sở thích, gia đình',
    subs: ['dogs', 'cats', 'Teachers', 'nursing', 'Fishing', 'camping', 'gardening', 'Mommit', 'daddit', 'Veterans'],
  },
  {
    id: 'holidays',
    label: 'Mùa lễ',
    title: 'Dịp lễ & quà tặng tại Mỹ',
    subs: ['Thanksgiving', 'Christmas', 'Halloween', 'GiftIdeas', 'crafts'],
  },
  {
    id: 'bifl',
    label: 'Đồ bền & Độc lạ',
    title: 'Sản phẩm bền, đồ lạ',
    subs: ['BuyItForLife', 'gadgets', 'DidntKnowIWantedThat'],
  },
  {
    id: 'viral_shopping',
    label: 'Viral Shopping',
    title: 'Sản phẩm viral trên TikTok/Amazon',
    subs: ['TikTokshop', 'AmazonWTF', 'shutupandtakemymoney'],
  },
  {
    id: 'tech',
    label: 'Tech & Hardware',
    title: 'Công nghệ & phần cứng',
    subs: ['gadgets', 'technology', 'hardware'],
  },
];
