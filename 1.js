//================================================================================
// 공통 스크립트
// Flow 와 관련된 내용이 기술되어 있다.
// (submit, init 등)
//--------------------------------------------------------------------------------
// jQuery 1.8+ 버전 dependency
//--------------------------------------------------------------------------------
// 작성자 : 김지민
// 작성일자 : 2014.09.02
//================================================================================

var Message = ext.message;  // Message 설정
var lazyForm = null;  // lazy form
var lazyCallback = null;  // lazy callback



/**
 * 화면 초기화
 */
function initApp() {
    $(document).ready(function() {
        //------------------------------------------------------------
        // 현재 포커스 객체 저장
        //------------------------------------------------------------
        try {
            $("a, :input").bind('click focus', function(event) {
                currentFocusElement = $(this);
            });
        }
        catch(e) {}
        //------------------------------------------------------------
        // 중복 서밋 방지 해제.
        //------------------------------------------------------------
        isSubmit = false;
        //------------------------------------------------------------
        // Validation 객체 생성
        //------------------------------------------------------------
        ExtValidation = new ext.validation();
        //------------------------------------------------------------
        // 페이지 블럭 해제.
        //------------------------------------------------------------
        loadingBlock(false);
        //------------------------------------------------------------
        // PKI 설치 여부 확인
        //------------------------------------------------------------
        if(checkPki()) {
            PkiUtils.printTag(false);
            //------------------------------------------------------------
            if(!PkiUtils.isInstalled()) {
                Message.alert("구간암호화 모듈이 설치되어 있지 않습니다.<br />확인 버튼을 선택하시면 cab 파일 설치를 진행합니다.", function() {
                    PkiUtils.printTag(true);
                });
            }
        }
        //------------------------------------------------------------
        // 인증서 설치 여부 확인
        //------------------------------------------------------------
//        if(checkPkiCert()) {
//            PkiUtils.cert.printTag(false);
//            //------------------------------------------------------------
//            if(!PkiUtils.cert.isInstalled()) {
//                Message.alert("인증서 모듈이 설치되어 있지 않습니다.<br />확인 버튼을 선택하시면 설치 페이지로 이동합니다.<br />* 현재 설치페이지가 구성되어 있지 않기 때문에 cab 파일 설치를 진행합니다.", function() {
//                    PkiUtils.cert.printTag(true);
//                });
//            }
//        }
        //------------------------------------------------------------
        // 보고서 설치 여부 확인
        //------------------------------------------------------------
        ReportUtils.printTag(false);
        //------------------------------------------------------------
//        if(!ReportUtils.isInstalled()) {
//            Message.alert("보고서 모듈이 설치되어 있지 않습니다.<br />확인 버튼을 선택하시면 cab 파일 설치를 진행합니다.", function() {
//                ReportUtils.printTag(true);
//            });
//        }
    });
}


/**
 * 화면에서 onload 시에 수행되는 내용 작성.
 * form 단위 onload 기능을 수행한다.
 * (jQuery 의 $.ready 를 무분별하게 사용하면, init point 를 식별하기 어려운 문제가 있음)
 *
 * @param form
 * @param callback
 */
function formReady(form, callback) {
    $(document).ready(function() {
        var formObj  = getForm(form);
        var $formObj = $(formObj);
        //------------------------------------------------------------
        if(!formObj) {
            if(!lazyForm) {
                lazyForm = form;
                lazyCallback = callback;
            }
            //------------------------------------------------------------
            return;
        }
        //------------------------------------------------------------
        lazyForm = null;
        lazyCallback = null;
        //------------------------------------------------------------
        isSubmit = false;
        //------------------------------------------------------------
        // 폼 자동 서브밋 방지.
        //------------------------------------------------------------
        $formObj.bind("submit", function(event) {
            return false;
        });
        //------------------------------------------------------------
        // form 자동완성 off
        //------------------------------------------------------------
        $formObj.attr("autocomplete", "off");
        //------------------------------------------------------------
        // input field filter init
        //------------------------------------------------------------
        ExtValidation.initFilter(formObj);
        //------------------------------------------------------------
        // XXX 오류메시지 처리
        //------------------------------------------------------------
        var isError = false;
        var $isErrorMessageObj = $("#" + IS_ERROR_ATTRIBUTE_NAME);
        //------------------------------------------------------------
        if($isErrorMessageObj.length > 0 && $isErrorMessageObj.val() === "true") {
            isError = true;
            //------------------------------------------------------------
            var $errorMessageObj = $("#" + ERROR_MESSAGE_ATTRIBUTE_NAME);
            //------------------------------------------------------------
            Message.error($errorMessageObj.val(), function() {
                $isErrorMessageObj.val("");  // 에러FLAG 초기화
                $errorMessageObj.val("");    // 에러메시지 초기화
            });
        }
        //------------------------------------------------------------
        // 메시지 처리
        //------------------------------------------------------------
        var $messageObj = $("#" + MESSAGE_ATTRIBUTE_NAME);
        //------------------------------------------------------------
        if(!isError && $messageObj.length > 0 && $messageObj.val() != "") {
            Message.alert($messageObj.val(), function() {
                $messageObj.val("");  // 메시지 초기화
                //------------------------------------------------------------
                if(callback) {
                    callback(formObj);
                }
            });
        }
        else {
            if(callback) {
                callback(formObj);
            }
        }
    });
}


/**
 * form DOM object 를 반환한다.
 *
 * @param form fromName or formId
 * @returns form object
 */
function getForm(form) {
    var formObj = null;
    //------------------------------------------------------------
    if(typeof(form) == "object") {
        formObj = form;
    }
    else {
        var $formByName = $("form[name=" + form + "]");
        var $formById = $("form").find("#" + form);
        //------------------------------------------------------------
        if($formByName.length > 0) {
            formObj = $formByName[0];
        }
        else if($formById.length > 0) {
            formObj = $formById[0];
        }
    }
    //------------------------------------------------------------
    return formObj;
}


/**
 * 현재 새션의 Active 상태를 반환한다.
 */
function checkSession() {
    var result = false;
    //------------------------------------------------------------
    $.ajax({
        type: "post",
        cache: false,
        url: CONTEXT_PATH + "/common/check/session_check.jsp",
        async: false,
        dataType: "json",
        data: {},
        complete: function(data, status) {
            var resultJson = JSON.parse(data.responseText);
            result = resultJson.result;
        }
    });
    //------------------------------------------------------------
    return result;
}


/**
 * 현재 PKI의 Active 상태를 반환한다.
 */
function checkPki() {
    var result = false;
    //------------------------------------------------------------
    $.ajax({
        type: "post",
        cache: false,
        url: CONTEXT_PATH + "/common/check/pki_check.jsp",
        async: false,
        dataType: "json",
        data: {},
        complete: function(data, status) {
        	var resultJson = JSON.parse(data.responseText);
            result = resultJson.result;
        }
    });
    //------------------------------------------------------------
    return result;
}


/**
 * 현재 인증서의 Active 상태를 반환한다.
 */
function checkPkiCert() {
    var result = false;
    //------------------------------------------------------------
    $.ajax({
        type: "post",
        cache: false,
        url: CONTEXT_PATH + "/common/check/pki_cert_check.jsp",
        async: false,
        dataType: "json",
        data: {},
        complete: function(data, status) {
            var resultJson = JSON.parse(data.responseText);
            result = resultJson.result;
        }
    });
    //------------------------------------------------------------
    return result;
}


/**
 * 현재 휴대폰실명인증 의 Active 상태를 반환한다.
 */
function checkPpc() {
    var result = false;
    //------------------------------------------------------------
    $.ajax({
        type: "post",
        cache: false,
        url: CONTEXT_PATH + "/common/check/ppc_check.jsp",
        async: false,
        dataType: "json",
        data: {},
        complete: function(data, status) {
            var resultJson = JSON.parse(data.responseText);
            result = resultJson.result;
        }
    });
    //------------------------------------------------------------
    return result;
}


/**
 * Ajax Submit 을 수행한다.
 *
 * @param uri URI
 * @param param JSON 파라미터
 * @param callback callback function
 * @param isBizSkip [option] service skip 여부
 * @param isSkipSessionCheck [option] Session Check Skip 여부
 */
function ajaxSubmit(uri, param, callback, isBizSkip, isSkipSessionCheck) {
    if(!param) {
        param = {};
    }
    //------------------------------------------------------------
    // 중복 submit 방지
    //------------------------------------------------------------
    if(isSubmit) {
        return;
    }
    //------------------------------------------------------------
    // 중복 click 방지
    //------------------------------------------------------------
    if(currentFocusElement) {
        $(currentFocusElement).blur();
    }
    //------------------------------------------------------------
    // 화면 block
    //------------------------------------------------------------
    loadingBlock(true);
    //------------------------------------------------------------
    // 현재 세션 유효성 체크
    //------------------------------------------------------------
    var sessionState = (isSkipSessionCheck) ? true : checkSession();
    //var sessionState = true;
    //------------------------------------------------------------
    if(sessionState) {
        param.isProcess = (isBizSkip) ? "false" : "true";
        //------------------------------------------------------------
        isSubmit = true;
        //------------------------------------------------------------
        // 구간암호화
        //------------------------------------------------------------
        if(checkPki()) {
            PkiUtils.setEncryptDataWithAjax(param, PkiUtils.getEncryptDataWithAjax(param));
        }
        //------------------------------------------------------------
        // Call Ajax
        //------------------------------------------------------------
        $.ajax({
            type: "POST",
            cache: false,
            url: uri,
            dataType: "json",
            data: param,
            success: function(data, status) {
            },
            error: function(req, status, error) {
                Message.alert("오류가 발생하였습니다.\n\n[status] " + status + "\n[error] " + error);
            },
            complete: function(data, status) {
                //------------------------------------------------------------
                // 현재 포커스 객체 저장
                //------------------------------------------------------------
                try {
                    $("a, :input").bind("click focus", function(event) {
                        currentFocusElement = $(this);
                    });
                }
                catch(e) {}
                //------------------------------------------------------------
                // 중복 서밋 방지 해제.
                //------------------------------------------------------------
                isSubmit = false;
                //------------------------------------------------------------
                // 페이지 블럭 해제.
                //------------------------------------------------------------
                loadingBlock(false);
                //------------------------------------------------------------
                data.responseText = StringUtil.replaceAll(data.responseText, "&#40;", "(");
                data.responseText = StringUtil.replaceAll(data.responseText, "&#41;", ")");
                //------------------------------------------------------------
                var resultJson = JSON.parse(data.responseText);
                //var resultJson = data.responseJSON;
                //------------------------------------------------------------
                if(status === "success") {
                    resultJson.isError = false;
                    resultJson.errorMsg = "";
                    //------------------------------------------------------------
                    // XXX 오류메시지 처리
                    //------------------------------------------------------------
                    var isError = resultJson[IS_ERROR_ATTRIBUTE_NAME];
                    //------------------------------------------------------------
                    if(isError === true || isError === "true") {
                        isError = true;
                        //------------------------------------------------------------
                        var errorMessage = resultJson[ERROR_MESSAGE_ATTRIBUTE_NAME];
                        //------------------------------------------------------------
                        Message.error(errorMessage);
                        //------------------------------------------------------------
                        resultJson.isError = true;
                        resultJson.errorMsg = errorMessage;
                    }
                    //------------------------------------------------------------
                    // 메시지 처리
                    //------------------------------------------------------------
                    var resultMessage = resultJson[MESSAGE_ATTRIBUTE_NAME];
                    //------------------------------------------------------------
                    if(!isError && resultMessage && resultMessage !== "") {
                        Message.alert(resultMessage);
                    }
                }
                else {
                    resultJson = {};
                    resultJson.isError = true;
                    resultJson.errorMsg = status;
                }
                //------------------------------------------------------------
                // callback function 호출
                //------------------------------------------------------------
                AJAX_PAGING_CALLBACK = null;
                //------------------------------------------------------------
                if(callback) {
                    callback(resultJson);
                }
            }
        });
    }
    else {
        Message.alert("세션이 만료되었습니다.\n[확인] 버튼을 누르시면 메인 페이지로 이동합니다.", function() {
            if(window.dialogArguments) {
                WindowUtil.closeModalPopup(null);
            }
            else {
                goMain();
            }
        });
    }
}



/**
 * submit 을 수행한다.
 *
 * @param form formName or formID
 * @param isBizSkip [option] service skip 여부
 * @param _target [option] target frameName
 * @param certOptions [option] 인증서관련옵션
 * @param ppcOptions [option] 휴대폰관련옵션
 */
function formSubmit(form, isBizSkip, _target, certOptions, ppcOptions) {
    var formObj = getForm(form);
    //------------------------------------------------------------
    // Validation Check
    //------------------------------------------------------------
    if(!ExtValidation.validate(formObj)) {
        return;
    }
    //------------------------------------------------------------
    // 인증서 Check
    //------------------------------------------------------------
    if(certOptions && certOptions["isCert"] === true) {
        PkiUtils.cert.setCertVidData(formObj, certOptions["certVid"], certOptions["certType"]);
        //------------------------------------------------------------
        if(checkPkiCert()) {
            if(!PkiUtils.cert.setCertData(formObj, certOptions["certVid"], certOptions["certType"])) {
                return;
            }
        }
    }
    //------------------------------------------------------------
    // 휴대폰인증 check
    //------------------------------------------------------------
    if(ppcOptions && ppcOptions["isPpc"] === true) {
        PpcUtil.setData(formObj, ppcOptions);
    }
    //------------------------------------------------------------
    // 중복 submit 방지
    //------------------------------------------------------------
    if(isSubmit) {
        return;
    }
    //------------------------------------------------------------
    // 중복 click 방지
    //------------------------------------------------------------
    if(currentFocusElement) {
        $(currentFocusElement).blur();
    }
    //------------------------------------------------------------
    // 화면 block
    //------------------------------------------------------------
    loadingBlock(true);
    //------------------------------------------------------------
    var $formObj = $(formObj);
    //------------------------------------------------------------
    $formObj.find("input[name=isProcess]").remove();
    $formObj.append('<input type="hidden" name="isProcess" value="' + ((isBizSkip) ? "false" : "true") + '" />');
    //------------------------------------------------------------
    $formObj.attr("method", "post");
    //------------------------------------------------------------
    if (_target != null && _target != "") {
        $formObj.attr("target", _target);
    }
    //------------------------------------------------------------
    isSubmit = true;
    //------------------------------------------------------------
    // 구간암호화
    //------------------------------------------------------------
    if(checkPki()) {
        PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj));
    }
    //------------------------------------------------------------
    if(formObj != null) 
        formObj.submit();
    else
        $formObj.submit();
}



/**
 * uploadSubmit 을 수행한다.
 */
function uploadSubmit(form, isBizSkip, _target, isSkipSessionCheck) {
    //------------------------------------------------------------
    // 현재 세션 유효성 체크
    //------------------------------------------------------------
    var sessionState = (isSkipSessionCheck) ? true : checkSession();
    //------------------------------------------------------------
    if(sessionState) {
        var $form = $(getForm(form));
        //--------------------------------------------------------------------------------
        var orgEncType = $form.attr("enctype");        
        $form.attr("enctype", "multipart/form-data");
        //--------------------------------------------------------------------------------
        formSubmit(form, isBizSkip, _target);
        //--------------------------------------------------------------------------------
        $form.attr("enctype", orgEncType);
    }
    else {
        Message.alert("세션이 만료되었습니다.\n[확인] 버튼을 누르시면 메인 페이지로 이동합니다.", function() {
            if(window.dialogArguments) {
                WindowUtil.closeModalPopup(null);
            }
            else {
                goMain();
            }
        });
    }
}


/**
 * 메뉴를 이동한다.
 *
 * @param menuId 메뉴ID
 * @param isUri [option] uri여부
 */
function goMenu(menuId, isUri) {
    var $menuForm = $(getForm("_menuForm"));
    //------------------------------------------------------------
    if(isUri) {
        $menuForm.attr("action", CONTEXT_PATH + menuId);
    }
    else {
        $menuForm.attr("action", CONTEXT_PATH + "/menu.do");
        $menuForm.find("input[name=menuId]").val(menuId);
    }
    //------------------------------------------------------------
    formSubmit($menuForm[0], true);
}


/**
 * 상세화면에서 목록 화면으로 이동한다.
 *
 * @param param 파라미터
 */
function goList(param) {
    var $menuForm = $(getForm("_menuForm"));
    //------------------------------------------------------------
    $menuForm.attr("action", CONTEXT_PATH + "/list.do");
    //------------------------------------------------------------
    if(param) {
        for(var i in param) {
            $menuForm.append('<input type="hidden" name="' + i + '" value="' + param[i] + '" />');
        }
    }
    //------------------------------------------------------------
    formSubmit($menuForm[0], true);
}


/**
 * 로그인을 수행한다.
 */
function login() {
    var $loginForm = $(getForm("_loginForm"));
    $loginForm.attr("action", CONTEXT_PATH + "/j_spring_security_check");
    formSubmit($loginForm[0]);
}


/**
 * 로그아웃을 수행한다.
 */
function logout() {
    var $loginForm = $(getForm("_loginForm"));
    $loginForm.attr("action", CONTEXT_PATH + "/logout.do");
    formSubmit($loginForm[0]);
}


/**
 * (포탈)로그인을 수행한다.
 */
function portalLogin(form, mberTy, certOptions, ppcOptions) {
    var $loginForm = $(getForm(form));
    var uriType = "makr";
    //--------------------------------------------------------------------------------
    if(mberTy === "P30") {
        uriType = "agency";
    }
    else if(mberTy === "P40") {
        uriType = "purchsr";
    }
    //--------------------------------------------------------------------------------
    $loginForm.attr("action", CONTEXT_PATH + "/" + uriType + "/j_spring_security_check");
    //--------------------------------------------------------------------------------
    formSubmit($loginForm[0], null, null, certOptions, ppcOptions);
}


/**
 * (포탈)로그아웃을 수행한다.
 */
function portalLogout() {
    var $loginForm = $(getForm("_loginForm"));
    //--------------------------------------------------------------------------------
    $loginForm.attr("action", CONTEXT_PATH + "/logout.do");
    //--------------------------------------------------------------------------------
    formSubmit($loginForm[0]);
}


/**
 * 메인화면으로 이동한다.
 */
function goMain() {
    var $menuForm = $(getForm("_menuForm"));
    //------------------------------------------------------------
    //console.log($menuForm);
    //console.log("goMain CONTEXT_PATH="+CONTEXT_PATH+ " : "+$menuForm[0]);
    $menuForm.attr("action", CONTEXT_PATH + "/");
    //------------------------------------------------------------
    formSubmit($menuForm[0], true);
}


/**
 * (포탈)회원가입 화면으로 이동한다.
 */
function portalSignIn() {
    var $loginForm = $(getForm("_menuForm"));
    //--------------------------------------------------------------------------------
    $loginForm.attr("action", CONTEXT_PATH + "/P070001001SF01.do");
    //--------------------------------------------------------------------------------
    formSubmit($loginForm[0]);
}


/**
 * (포탈)마이페이지 화면으로 이동한다.
 */
function portalGoMyPage(mberTy) {
    var resultUri = "";
    //--------------------------------------------------------------------------------
    switch(mberTy) {
        case "P40":
            resultUri = "/purchsr/P070002000SF01.do";
            break;
    }
    //--------------------------------------------------------------------------------
    if(resultUri !== "") {
        goMenu(resultUri, true);
    }
}


/**
 * 로딩 Block
 * (submit 등등..)
 * @param isBlock
 */
function loadingBlock(isBlock) {
    if(isBlock) {
        if (!lodingExtBlock && isShowBlocking) {
            lodingExtBlock = new ext.Block();
            lodingExtBlock.show(isShowLoadingImg ? LOADING_WRAP_LAYER : null, {
                show: true,
                focus: false,
                addTop : -50
            }, null);
        }
    }
    else {
        if (lodingExtBlock && !isRetainBlocking) {
            lodingExtBlock.beforeFocus = false; // 이전 포커스 금지.
            lodingExtBlock.hide();
            lodingExtBlock = null;
        }
        //------------------------------------------------------------
        isShowBlocking = true;
        isShowLoadingImg = true;
    }
}


/**
 * paging 이동 기능을 수행한다.
 * (paging tag 에서 내부적으로 사용된다)
 *
 * @param formName formName or formID
 * @param pageIndex Page Index
 */
function _paging(formName, pageIndex) {
    var $formObj   = $(getForm(formName));
    var $pageIndex = $formObj.find("input[name=pageIndex]");
    //------------------------------------------------------------
    if($pageIndex.length > 0) {
        $pageIndex.val(pageIndex);
    }
    else {
        $formObj.append('<input type="hidden" name="pageIndex" value="' + pageIndex + '" />');
    }
    //------------------------------------------------------------
    formSubmit(formName);
}


/**
 * Ajax 용 paging 이동 기능을 수행한다.
 * (Ajax paging 에서 내부적으로 사용된다)
 *
 * @param pageNo 페이지번호
 * @param url    URl
 * @param param  Parameter
 * @param isSkipSessionCheck  세션체크skip여부
 */
function _pagingAjax(pageNo, url, param, isSkipSessionCheck) {
    param = JSON.parse(unescape(param));
    param.pageIndex = pageNo;
    ajaxSubmit(url, param, AJAX_PAGING_CALLBACK, null, isSkipSessionCheck);
}


/**
 * Ajax 용 paging 을 표시한다.
 *
 * @param elementId  paging 이 표현될 ElementId
 * @param pagingInfo PagingInfo
 * @param url        URL
 * @param param      Parameter[json]
 * @param callback
 * @param isSkipSessionCheck 세션체크skip여부
 */
function showAjaxPaging(elementId, pagingInfo, url, param, callback, isSkipSessionCheck) {
    param = escape((!param || param == null) ? "{}" : JSON.stringify(param));
    //------------------------------------------------------------
    AJAX_PAGING_CALLBACK = callback;
    isSkipSessionCheck = (isSkipSessionCheck) ? true : false;
    //------------------------------------------------------------
    var pagingHtml = "";
    //------------------------------------------------------------
    if(pagingInfo.totalPageCount > pagingInfo.pageSize) {
        if(pagingInfo.firstPageNoOnPageList > pagingInfo.pageSize) {
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + pagingInfo.firstPageNo + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="prev_first"><img src="' + CONTEXT_PATH + '/docs/img/prev_first.png" height="25" width="25" alt="처음 페이지" /></a>';
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + (pagingInfo.firstPageNoOnPageList - 1) + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="prev"><img src="' + CONTEXT_PATH + '/docs/img/prev.png" height="25" width="25" alt="이전 페이지" /></a>';
        }
        else {
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + pagingInfo.firstPageNo + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="prev_first"><img src="' + CONTEXT_PATH + '/docs/img/prev_first.png" height="25" width="25" alt="처음 페이지" /></a>';
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + pagingInfo.firstPageNo + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="prev"><img src="' + CONTEXT_PATH + '/docs/img/prev.png" height="25" width="25" alt="이전 페이지" /></a>';
        }
    }
    //------------------------------------------------------------
    for(var i=pagingInfo.firstPageNoOnPageList; i <= pagingInfo.lastPageNoOnPageList; i++) {
        if(i == pagingInfo.currentPageNo) {
            pagingHtml += '<a href="#" class="on">' + i + '</a>';
        }
        else {
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + i + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');">' + i + '</a>';
        }
    }
    //------------------------------------------------------------
    if(pagingInfo.totalPageCount > pagingInfo.pageSize) {
        if(pagingInfo.lastPageNoOnPageList < pagingInfo.totalPageCount) {
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + (pagingInfo.firstPageNoOnPageList + pagingInfo.pageSize) + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="next"><img src="' + CONTEXT_PATH + '/docs/img/next.png" height="25" width="25" alt="다음 페이지" /></a>';
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + pagingInfo.lastPageNo + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="next_last"><img src="' + CONTEXT_PATH + '/docs/img/next_last.png" height="25" width="25" alt="마지막 페이지" /></a>';
        }
        else {
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + pagingInfo.lastPageNo + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="next"><img src="' + CONTEXT_PATH + '/docs/img/next.png" height="25" width="25" alt="다음 페이지" /></a>';
            pagingHtml += '<a href="javascript:' + AJAX_PAGING_SUBMIT_FUNC_NAME + '(' + pagingInfo.lastPageNo + ', \'' + url + '\', \'' + param + '\', ' + isSkipSessionCheck + ');" class="next_last"><img src="' + CONTEXT_PATH + '/docs/img/next_last.png" height="25" width="25" alt="마지막 페이지" /></a>';
        }
    }
    //------------------------------------------------------------
    var $parentElement = $("#" + elementId).parent();
    //------------------------------------------------------------
    $parentElement.find("#" + elementId).remove();
    $parentElement.append('<div id="' + elementId + '"></div>');
    $parentElement.find("#" + elementId).addClass("paginate").append(pagingHtml);    
}


/**
 * 파일 다운로드를 수행한다.
 *
 * @param fileId    파일ID
 * @param atchbrdNo 게시물번호
 * @param isSkipSessionCheck 세션체크skip여부
 */
function fileDownload(fileId, atchbrdNo, isSkipSessionCheck) {
    //------------------------------------------------------------
    // 현재 세션 유효성 체크
    //------------------------------------------------------------
    var sessionState = (isSkipSessionCheck) ? true : checkSession();
    //------------------------------------------------------------
    if(sessionState) {
        var $iframeObj = $("#downloadFrame");
        if($iframeObj.length < 1) {
            $("body").append('<iframe name="downloadFrame" id="downloadFrame" width="0" height="0" style="display:none;"></iframe>');
        }
        //------------------------------------------------------------
        var formObj = getForm("downLoadForm");
        //------------------------------------------------------------
        if(!formObj) {
            // 히든폼 추가
            $("body").append('<form name="downLoadForm" id="downloadForm"></form>');
            formObj = getForm("downLoadForm");
        }
        //------------------------------------------------------------
        var $form = $(formObj);
        //------------------------------------------------------------
        $form.remove("input");
        //------------------------------------------------------------
        $form.append('<input type="hidden" name="fileId" value="' + fileId + '" />');
        $form.append('<input type="hidden" name="atchbrdNo" value="' + atchbrdNo + '" />');
        //------------------------------------------------------------
        $form.attr("action", CONTEXT_PATH + "/download.do");
        $form.attr("method", "post");
        $form.attr("target", "downloadFrame");
        //------------------------------------------------------------
        // 구간암호화
        //------------------------------------------------------------
        if(checkPki()) {
            PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj));
        }
        //------------------------------------------------------------
        formObj.submit();
        //------------------------------------------------------------
        $form.remove();
        //------------------------------------------------------------
        return false;
    }
    else {
        Message.alert("세션이 만료되었습니다.\n[확인] 버튼을 누르시면 메인 페이지로 이동합니다.", function() {
            if(window.dialogArguments) {
                WindowUtil.closeModalPopup(null);
            }
            else {
                goMain();
            }
        });
    }
}


/**
 * (양식)파일 다운로드를 수행한다.
 *
 * @param dtlCd 상세코드
 * @param isSkipSessionCheck 세션체크skip여부
 */
function docFileDownload(dtlCd, isSkipSessionCheck) {
    //------------------------------------------------------------
    // 현재 세션 유효성 체크
    //------------------------------------------------------------
    var sessionState = (isSkipSessionCheck) ? true : checkSession();
    //------------------------------------------------------------
    if(sessionState) {
        var $iframeObj = $("#downloadFrame");
        if($iframeObj.length < 1) {
            $("body").append('<iframe name="downloadFrame" id="downloadFrame" width="0" height="0" style="display:none;"></iframe>');
        }
        //------------------------------------------------------------
        var formObj = getForm("downLoadForm");
        //------------------------------------------------------------
        if(!formObj) {
            // 히든폼 추가
            $("body").append('<form name="downLoadForm" id="downloadForm"></form>');
            formObj = getForm("downLoadForm");
        }
        //------------------------------------------------------------
        var $form = $(formObj);
        //------------------------------------------------------------
        $form.remove("input");
        //------------------------------------------------------------
        $form.append('<input type="hidden" name="dtlCd" value="' + dtlCd + '" />');
        //------------------------------------------------------------
        $form.attr("action", CONTEXT_PATH + "/docDownload.do");
        $form.attr("method", "post");
        $form.attr("target", "downloadFrame");
        //------------------------------------------------------------
        // 구간암호화
        //------------------------------------------------------------
        if(checkPki()) {
            PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj));
        }
        //------------------------------------------------------------
        formObj.submit();
        //------------------------------------------------------------
        $form.remove();
        //------------------------------------------------------------
        return false;
    }
    else {
        Message.alert("세션이 만료되었습니다.\n[확인] 버튼을 누르시면 메인 페이지로 이동합니다.", function() {
            if(window.dialogArguments) {
                WindowUtil.closeModalPopup(null);
            }
            else {
                goMain();
            }
        });
    }
}


/**
 * Grid 의 데이터를 excel 로 export 한다.
 */
function exportExcel(elementId, excludeList) {
    if(checkSession()) {
        var $gridMenuList = $("#" + elementId);
        //--------------------------------------------------------------------------------
        var colNames = GridUtil.getParam(elementId, "colNames");
        var colModel = GridUtil.getParam(elementId, "colModel");
        var headers  = [];
        var columns  = [];
        //--------------------------------------------------------------------------------
        for(var i=0; i < colNames.length; i++) {
            if(colNames[i].indexOf("<") !== 0) {
                if(excludeList && excludeList.length > 0 && ($.inArray(colModel[i].name, excludeList) > -1)) {
                    continue;
                }
                //--------------------------------------------------------------------------------
                headers.push(colNames[i]);
                columns.push(colModel[i].name);
            }
        }
        //--------------------------------------------------------------------------------
        var jsonData = {};
        //--------------------------------------------------------------------------------
        jsonData.listName = "gridList";
        //--------------------------------------------------------------------------------
        jsonData.headers = headers;
        jsonData.columns = columns;
        //--------------------------------------------------------------------------------
        jsonData[jsonData.listName] = [];
        var gridRowData = $gridMenuList.jqGrid("getRowData");
        //--------------------------------------------------------------------------------
        for(var i=0; i < gridRowData.length; i++) {
            jsonData[jsonData.listName][i] = {};
            //--------------------------------------------------------------------------------
            for(var j=0; j < jsonData.columns.length; j++) {
                jsonData[jsonData.listName][i][jsonData.columns[j]] = gridRowData[i][jsonData.columns[j]];
            }
        }
        //--------------------------------------------------------------------------------
        if(jsonData[jsonData.listName].length > 0) {
            var $iframeObj = $("#downloadFrame");
            if($iframeObj.length < 1) {
                $("body").append('<iframe name="downloadFrame" id="downloadFrame" width="0" height="0" style="display:none;"></iframe>');
            }
            //------------------------------------------------------------
            var formObj = getForm("excelDownLoadForm");
            //------------------------------------------------------------
            if(!formObj) {
                $("body").append('<form name="excelDownLoadForm" id="excelDownLoadForm"></form>');
                formObj = getForm("excelDownLoadForm");
            }
            //------------------------------------------------------------
            var $form = $(formObj);
            //------------------------------------------------------------
            $form.remove("input");
            //------------------------------------------------------------
            var appendHtml = "";
            //------------------------------------------------------------
            appendHtml += '<input type="hidden" name="listName"                  value=\'' + jsonData.listName                           + '\' />';
            appendHtml += '<input type="hidden" name="' + jsonData.listName + '" value=\'' + JSON.stringify(jsonData[jsonData.listName]) + '\' />';
            appendHtml += '<input type="hidden" name="headers"                   value=\'' + JSON.stringify(jsonData.headers)            + '\' />';
            appendHtml += '<input type="hidden" name="columns"                   value=\'' + JSON.stringify(jsonData.columns)            + '\' />';
            //------------------------------------------------------------
            $form.append(appendHtml);
            //------------------------------------------------------------
            $form.attr("action", CONTEXT_PATH + "/exportGridExcel.do");
            $form.attr("method", "post");
            $form.attr("target", "downloadFrame");
            //------------------------------------------------------------
            // 구간암호화
            //------------------------------------------------------------
            if(checkPki()) {
                PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj));
            }
            //------------------------------------------------------------
            formObj.submit();
            //------------------------------------------------------------
            $form.remove();
        }
        else {
            Message.alert("export 대상 데이터가 없습니다.");
        }
    }
    else {
        Message.alert("세션이 만료되었습니다.\n[확인] 버튼을 누르시면 메인 페이지로 이동합니다.", function() {
            if(window.dialogArguments) {
                WindowUtil.closeModalPopup(null);
            }
            else {
                goMain();
            }
        });
    }
}


/**
 * 테이블의 데이터를 excel 로 export 한다.
 */
function exportTblExcel(tblId) {
    if(checkSession()) {
        var $tblObj = $("#" + tblId);
        //--------------------------------------------------------------------------------
        var headers  = [];
        var columns  = [];
        //--------------------------------------------------------------------------------
        $tblObj.find("thead").find("th").each(function(idx) {
            var thText = $(this).text().trim();
            if(thText !== "") {
                headers.push(thText);
                columns.push(idx);
            }
        });
        //--------------------------------------------------------------------------------
        var jsonData = {};
        //--------------------------------------------------------------------------------
        jsonData.listName = "tblList";
        //--------------------------------------------------------------------------------
        jsonData.headers = headers;
        jsonData.columns = columns;
        //--------------------------------------------------------------------------------
        jsonData[jsonData.listName] = [];
        //--------------------------------------------------------------------------------
        $tblObj.find("tbody").find("tr").each(function(idx) {
            jsonData[jsonData.listName][idx] = {};
            //--------------------------------------------------------------------------------
            for(var j=0; j < jsonData.columns.length; j++) {
                jsonData[jsonData.listName][idx][jsonData.columns[j]] = $(this).find("td").eq(jsonData.columns[j]).text().trim();
            }
        });
        //--------------------------------------------------------------------------------
        if(jsonData[jsonData.listName].length > 0) {
            var $iframeObj = $("#downloadFrame");
            if($iframeObj.length < 1) {
                $("body").append('<iframe name="downloadFrame" id="downloadFrame" width="0" height="0" style="display:none;"></iframe>');
            }
            //------------------------------------------------------------
            var formObj = getForm("excelDownLoadForm");
            //------------------------------------------------------------
            if(!formObj) {
                $("body").append('<form name="excelDownLoadForm" id="excelDownLoadForm"></form>');
                formObj = getForm("excelDownLoadForm");
            }
            //------------------------------------------------------------
            var $form = $(formObj);
            //------------------------------------------------------------
            $form.remove("input");
            //------------------------------------------------------------
            var appendHtml = "";
            //------------------------------------------------------------
            appendHtml += '<input type="hidden" name="listName"                  value=\'' + jsonData.listName                           + '\' />';
            appendHtml += '<input type="hidden" name="' + jsonData.listName + '" value=\'' + JSON.stringify(jsonData[jsonData.listName]) + '\' />';
            appendHtml += '<input type="hidden" name="headers"                   value=\'' + JSON.stringify(jsonData.headers)            + '\' />';
            appendHtml += '<input type="hidden" name="columns"                   value=\'' + JSON.stringify(jsonData.columns)            + '\' />';
            //------------------------------------------------------------
            $form.append(appendHtml);
            //------------------------------------------------------------
            $form.attr("action", CONTEXT_PATH + "/exportTblExcel.do");
            $form.attr("method", "post");
            $form.attr("target", "downloadFrame");
            //------------------------------------------------------------
            // 구간암호화
            //------------------------------------------------------------
            if(checkPki()) {
                PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj));
            }
            //------------------------------------------------------------
            formObj.submit();
            //------------------------------------------------------------
            $form.remove();
        }
        else {
            Message.alert("export 대상 데이터가 없습니다.");
        }
    }
    else {
        Message.alert("세션이 만료되었습니다.\n[확인] 버튼을 누르시면 메인 페이지로 이동합니다.", function() {
            if(window.dialogArguments) {
                WindowUtil.closeModalPopup(null);
            }
            else {
                goMain();
            }
        });
    }
}


/**
 * 현재 페이지를 reload 한다.
 */
function reload() {
    var currentUrl = window.location.href;
    //------------------------------------------------------------
    // 화면 block
    //------------------------------------------------------------
    loadingBlock(true);
    //------------------------------------------------------------
    isSubmit = true;
    //------------------------------------------------------------
    if(currentUrl.lastIndexOf("#") > -1) {
        currentUrl = currentUrl.substring(0, currentUrl.lastIndexOf("#"));
    }
    //------------------------------------------------------------
    if(window.dialogArguments) {
        var reloadFormName = "_reloadForm";
        //------------------------------------------------------------
        $("body").append('<form name="' + reloadFormName + ' id="' + reloadFormName + '"></form>');
        //------------------------------------------------------------
        var reloadFormObj = getForm("_reloadForm");
        var $reloadForm = $("form[name=_reloadForm]");
        //------------------------------------------------------------
        $reloadForm.attr("method", "post");
        $reloadForm.attr("action", currentUrl);
        //------------------------------------------------------------
        // 구간암호화
        //------------------------------------------------------------
        if(checkPki()) {
            PkiUtils.setEncryptData(reloadFormObj, PkiUtils.getEncryptData(reloadFormObj));
        }
        //------------------------------------------------------------
        reloadFormObj.submit();
    }
    else {
        window.document.location.href = currentUrl;
    }
}


function goExtraLinkPage(url, target) {
    top.window.open(url, (target) ? target : "_blank");
}



initApp();  // 화면초기화 수행
