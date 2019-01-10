var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = true;   // 是否正在向后台获取数据


$(function () {
    // 界面加载完成之后去加载数据
    updateVideosData();
    // 首页分类切换
    $('#index li').click(function () {
        // 取到指定分类的cid
        var clickCid = $(this).attr('data-cid');
        // 遍历所有的 li 移除身上的选中效果
        $('#index li').each(function () {
            $(this).removeClass('active')
        });
        // 给当前分类添加选中的状态
        $(this).addClass('active');
        // 如果点击的分类与当前分类不一致
        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid;

            // 重置分页参数
            cur_page = 1
            total_page = 1
            updateVideosData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            // 判断页数，去更新新闻数据

            if (!data_querying) {
                data_querying = true

                // 如果当前页数据如果小于总页数，那么才去加载数据
                if (cur_page < total_page) {
                    cur_page += 1
                    // 去加载数据
                    updateVideosData()
                }

            }
        }
    })

})

function updateVideosData() {
    // 更新新闻数据
    var params = {
        "cid": currentCid,
        "page": cur_page
    }
    $.get("/video_list", params, function (resp) {
        // 数据加载完毕，设置【正在加载数据】的变量为 false 代表当前没有在加载数据
        data_querying = false
        if (resp.errno == "0") {
            // 给总页数据赋值
            total_page = resp.data.total_page
            // 代表请求成功
            // 清除已有数据
            if (cur_page == 1) {
                $("#video_id").html("");
            }
            for (var i=0;i<resp.data.video_dict_li.length;i++) {
                var video = resp.data.video_dict_li[i]
                var content = '<li>'
                content += '<a href="/videos/'+video.id +'" class="video_pic fr"><img src="../../static/uploads/'+ video.img_url +'"></a>'
                content += '<div class="con_box"><a href="'+ video.id+'" systemidvaule="'+video.id+'"><h3>'+ video.intro+'</h3></a>'
                content += '<span>永胜学院&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>'
                content += '<span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;播放次数：'+ video.clicks+'</span></div>'
                $(".list_con").append(content)
            }
        }else {
            // 请求失败
            console.log(resp.errmsg)
        }
	$('#video_id').delegate('a','click',function(){
              var sCode = $(this).attr('systemidvaule');
              $.ajax({
                  url:'/videos',
                  type:'get',
                  dataType:'text',
                  data:{'code':sCode}
              }).done(function(dat){
                if (dat.user=="False"){
                $('.login_form_con').show()
                }else{
                  window.href='play.html'
                }
              })
          })

    })
}


